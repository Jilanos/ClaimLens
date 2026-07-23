"""Local HTML process page for one-video runs."""

from __future__ import annotations

import html
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from claimlens import db
from claimlens.analysis import OpenAIAnalysisClient, analyze_cleaned_transcript
from claimlens.briefs import generate_brief, generate_verified_brief
from claimlens.config import AppConfig
from claimlens.pipeline import (
    clean_run_transcript,
    create_run,
    extract_required_subtitles,
    next_eligible_step,
)
from claimlens.verification import default_adapters, verify_sources


def serve_process_page(config: AppConfig, *, host: str, port: int) -> None:
    database_path = config.paths.database
    db.init_db(database_path)

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            query = parse_qs(parsed.query)
            run_id = _int_value(query.get("run_id", [""])[0])
            body = render_process_page(database_path, run_id=run_id)
            self._send_html(body)

        def do_POST(self) -> None:  # noqa: N802
            length = int(self.headers.get("Content-Length", "0"))
            form = parse_qs(self.rfile.read(length).decode("utf-8"))
            action = form.get("action", [""])[0]
            run_id: int | None = None
            try:
                if action == "create":
                    run_id = create_run(database_path, form.get("video_url", [""])[0])
                else:
                    run_id = int(form.get("run_id", [""])[0])
                    _run_action(config, database_path, run_id, action, form)
            except Exception as exc:
                body = render_process_page(database_path, run_id=run_id, notice=str(exc))
                self._send_html(body, status=400)
                return

            self.send_response(303)
            self.send_header("Location", f"/?run_id={run_id}")
            self.end_headers()

        def log_message(self, format: str, *args: object) -> None:
            return

        def _send_html(self, body: str, *, status: int = 200) -> None:
            encoded = body.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

    server = ThreadingHTTPServer((host, port), Handler)
    print(f"ClaimLens process page: http://{host}:{port}")
    server.serve_forever()


def render_process_page(
    database_path: Path | str,
    *,
    run_id: int | None = None,
    notice: str | None = None,
) -> str:
    selected_run = db.get_pipeline_run(database_path, run_id) if run_id else None
    runs = db.list_pipeline_runs(database_path)
    rows = ""
    controls = ""
    outputs = ""

    if selected_run is not None:
        step_rows = db.list_run_steps(database_path, selected_run["id"])
        rows = "\n".join(_step_row(row) for row in step_rows)
        next_step = next_eligible_step(database_path, selected_run["id"])
        controls = _controls(selected_run["id"], next_step)
        outputs = _outputs(database_path, selected_run["video_id"])

    run_options = "\n".join(
        f'<option value="{row["id"]}">#{row["id"]} {html.escape(row["video_id"] or "")}'
        f' - {html.escape(row["status"])}</option>'
        for row in runs
    )
    notice_html = f'<p class="notice">{html.escape(notice)}</p>' if notice else ""

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ClaimLens Process</title>
  <style>
    body {{ margin: 0; font-family: system-ui, sans-serif; color: #172026; background: #f6f7f8; }}
    main {{ max-width: 980px; margin: 0 auto; padding: 28px; }}
    section {{ margin: 22px 0; }}
    form {{ display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }}
    input, select {{
      min-height: 36px; padding: 6px 8px; border: 1px solid #aab4bd; border-radius: 4px;
    }}
    input[type="url"], input[type="password"] {{ flex: 1 1 280px; }}
    button {{
      min-height: 36px; padding: 6px 12px; border: 1px solid #172026; border-radius: 4px;
      background: #172026; color: white;
    }}
    table {{ width: 100%; border-collapse: collapse; background: white; }}
    th, td {{
      text-align: left; padding: 10px; border-bottom: 1px solid #d9dee2; vertical-align: top;
    }}
    .notice {{ padding: 10px; border: 1px solid #b8562f; background: #fff2ec; }}
    .status {{ font-weight: 700; }}
    a {{ color: #0a5c7a; }}
  </style>
</head>
<body>
<main>
  <h1>ClaimLens Process</h1>
  {notice_html}
  <section>
    <h2>Create Run</h2>
    <form method="post">
      <input type="hidden" name="action" value="create">
      <input name="video_url" type="url" required placeholder="https://www.youtube.com/watch?v=...">
      <button type="submit">Create</button>
    </form>
  </section>
  <section>
    <h2>Load Run</h2>
    <form method="get">
      <select name="run_id">{run_options}</select>
      <button type="submit">Load</button>
    </form>
  </section>
  <section>
    <h2>Steps</h2>
    <table>
      <thead><tr><th>Step</th><th>Status</th><th>Failure</th><th>Output</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>
    {controls}
  </section>
  {outputs}
</main>
</body>
</html>
"""


def _run_action(
    config: AppConfig,
    database_path: Path | str,
    run_id: int,
    action: str,
    form: dict[str, list[str]],
) -> None:
    run = db.get_pipeline_run(database_path, run_id)
    if run is None:
        raise ValueError(f"Run not found: {run_id}")

    if action == "captions":
        extract_required_subtitles(database_path, run_id)
    elif action == "clean_transcript":
        clean_run_transcript(database_path, run_id, outputs_path=config.paths.transcripts)
    elif action == "analysis":
        api_key = form.get("openai_api_key", [""])[0] or config.api_keys.openai
        client = OpenAIAnalysisClient(api_key=api_key)
        db.set_step_status(database_path, run_id=run_id, step="analysis", status="running")
        summary_id = analyze_cleaned_transcript(
            database_path,
            video_id=run["video_id"],
            client=client,
        )
        db.set_step_status(
            database_path,
            run_id=run_id,
            step="analysis",
            status="succeeded",
            output_path=f"sqlite:summaries/{summary_id}",
        )
        db.set_run_status(database_path, run_id=run_id, status="running", current_step="brief")
    elif action == "brief":
        path = generate_brief(
            database_path,
            video_id=run["video_id"],
            briefs_path=config.paths.briefs,
        )
        db.set_step_status(
            database_path,
            run_id=run_id,
            step="brief",
            status="succeeded",
            output_path=str(path),
        )
        db.set_run_status(database_path, run_id=run_id, status="succeeded", current_step="brief")
    elif action == "source_verification":
        semantic_key = (
            form.get("semantic_scholar_api_key", [""])[0]
            or config.api_keys.semantic_scholar
        )
        ncbi_key = form.get("ncbi_api_key", [""])[0] or config.api_keys.ncbi
        adapters = default_adapters(semantic_scholar_key=semantic_key, ncbi_key=ncbi_key)
        db.set_step_status(
            database_path,
            run_id=run_id,
            step="source_verification",
            status="running",
        )
        verification_run_id = verify_sources(
            database_path,
            video_id=run["video_id"],
            adapters=adapters,
            max_results=config.pipeline.source_verification_max_results,
            timeout_seconds=config.pipeline.source_verification_timeout_seconds,
        )
        path = generate_verified_brief(
            database_path,
            video_id=run["video_id"],
            briefs_path=config.paths.briefs,
        )
        db.set_step_status(
            database_path,
            run_id=run_id,
            step="source_verification",
            status="succeeded",
            output_path=str(path),
        )
        db.set_run_status(
            database_path,
            run_id=run_id,
            status="succeeded",
            current_step="source_verification",
        )
        _ = verification_run_id
    else:
        raise ValueError(f"Unsupported action: {action}")


def _controls(run_id: int, next_step: str | None) -> str:
    if next_step is None:
        return ""
    secret = ""
    if next_step == "analysis":
        secret = '<input name="openai_api_key" type="password" placeholder="OpenAI API key">'
    elif next_step == "source_verification":
        secret = (
            '<input name="semantic_scholar_api_key" type="password" '
            'placeholder="Semantic Scholar API key">'
            '<input name="ncbi_api_key" type="password" placeholder="NCBI API key">'
        )
    return f"""
    <form method="post">
      <input type="hidden" name="run_id" value="{run_id}">
      <input type="hidden" name="action" value="{html.escape(next_step)}">
      {secret}
      <button type="submit">Run {html.escape(next_step.replace("_", " "))}</button>
    </form>
    """


def _outputs(database_path: Path | str, video_id: str) -> str:
    cleaned = db.get_cleaned_transcript(database_path, video_id)
    brief = db.latest_brief_artifact(database_path, video_id)
    verification = db.latest_verification_run(database_path, video_id)
    links = []
    if cleaned is not None and cleaned["output_path"]:
        links.append(f"<li>Cleaned transcript: {html.escape(cleaned['output_path'])}</li>")
    if brief is not None:
        links.append(f"<li>Markdown brief: {html.escape(brief['path'])}</li>")
    if verification is not None:
        links.append(
            "<li>"
            f"Source verification: {html.escape(verification['status'])} "
            f"({_verification_counts(database_path, verification['id'])})"
            "</li>"
        )
    if not links:
        return ""
    return f"<section><h2>Outputs</h2><ul>{''.join(links)}</ul></section>"


def _verification_counts(database_path: Path | str, verification_run_id: int) -> str:
    evidence = db.evidence_for_verification(database_path, verification_run_id)
    supports = sum(1 for row in evidence if row["polarity"] == "supports")
    contradicts = sum(1 for row in evidence if row["polarity"] == "contradicts")
    return f"{supports} supporting snippets, {contradicts} contradicting snippets"


def _step_row(row) -> str:
    return (
        "<tr>"
        f"<td>{html.escape(row['step'].replace('_', ' '))}</td>"
        f"<td class=\"status\">{html.escape(row['status'])}</td>"
        f"<td>{html.escape(row['failure_message'] or '')}</td>"
        f"<td>{html.escape(row['output_path'] or '')}</td>"
        "</tr>"
    )


def _int_value(value: str) -> int | None:
    try:
        return int(value)
    except ValueError:
        return None
