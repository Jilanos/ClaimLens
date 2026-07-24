"""Local HTML process page for one-video runs."""

from __future__ import annotations

import html
import logging
import secrets
import time
from concurrent.futures import ThreadPoolExecutor
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

LOGGER = logging.getLogger(__name__)
EXECUTOR = ThreadPoolExecutor(max_workers=2, thread_name_prefix="claimlens-job")
RATE_LIMITS: dict[str, list[float]] = {}


def serve_process_page(config: AppConfig, *, host: str, port: int) -> None:
    database_path = config.paths.database
    db.init_db(database_path)
    csrf_token = secrets.token_urlsafe(32)

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            query = parse_qs(parsed.query)
            run_id = _int_value(query.get("run_id", [""])[0])
            if parsed.path == "/brief":
                self._send_html(
                    render_brief_page(database_path, config.paths.briefs, run_id=run_id)
                )
                return
            if parsed.path == "/brief/download":
                self._send_brief_download(database_path, config.paths.briefs, run_id=run_id)
                return
            body = render_process_page(database_path, run_id=run_id, csrf_token=csrf_token)
            self._send_html(body)

        def do_POST(self) -> None:  # noqa: N802
            try:
                form = self._read_form()
            except ValueError as exc:
                body = render_process_page(database_path, notice=str(exc), csrf_token=csrf_token)
                self._send_html(body, status=400)
                return
            if form.get("csrf_token", [""])[0] != csrf_token:
                body = render_process_page(
                    database_path,
                    notice="The form expired. Reload the page and try again.",
                    csrf_token=csrf_token,
                )
                self._send_html(body, status=403)
                return
            action = form.get("action", [""])[0]
            run_id: int | None = None
            try:
                _check_rate_limit(self.client_address[0], config)
                if action == "create":
                    run_id = create_run(
                        database_path,
                        form.get("video_url", [""])[0],
                        report_language=form.get(
                            "report_language",
                            [config.pipeline.report_language],
                        )[0],
                        fetch_metadata=True,
                    )
                else:
                    run_id = int(form.get("run_id", [""])[0])
                    job_id = db.create_job(database_path, run_id=run_id, action=action)
                    if job_id is None:
                        raise ValueError("This action is already queued or running for the run.")
                    EXECUTOR.submit(_run_job, config, database_path, run_id, action, form, job_id)
            except Exception as exc:
                LOGGER.info("Web action rejected: %s", exc)
                body = render_process_page(
                    database_path,
                    run_id=run_id,
                    notice=_public_error(exc),
                    csrf_token=csrf_token,
                )
                self._send_html(body, status=400)
                return

            self.send_response(303)
            self.send_header("Location", f"/?run_id={run_id}")
            self.end_headers()

        def log_message(self, format: str, *args: object) -> None:
            LOGGER.info("web access %s - %s", self.address_string(), format % args)

        def _read_form(self) -> dict[str, list[str]]:
            raw_length = self.headers.get("Content-Length", "0")
            try:
                length = int(raw_length)
            except ValueError as exc:
                raise ValueError("Invalid request length.") from exc
            if length < 0 or length > config.web.max_request_bytes:
                raise ValueError("Request body is too large.")
            return parse_qs(self.rfile.read(length).decode("utf-8"))

        def _send_html(self, body: str, *, status: int = 200) -> None:
            encoded = body.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def _send_brief_download(
            self,
            database_path: Path | str,
            briefs_path: Path | str,
            *,
            run_id: int | None,
        ) -> None:
            path = _brief_path_for_run(database_path, briefs_path, run_id)
            if path is None:
                self._send_html(
                    render_brief_page(database_path, briefs_path, run_id=run_id),
                    status=404,
                )
                return
            data = path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/markdown; charset=utf-8")
            self.send_header(
                "Content-Disposition",
                f'attachment; filename="{path.name.replace(chr(34), "")}"',
            )
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    server = ThreadingHTTPServer((host, port), Handler)
    print(f"ClaimLens process page: http://{host}:{port}")
    server.serve_forever()


def render_process_page(
    database_path: Path | str,
    *,
    run_id: int | None = None,
    notice: str | None = None,
    csrf_token: str = "",
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
        controls = _controls(selected_run["id"], next_step, csrf_token=csrf_token)
        outputs = _outputs(database_path, selected_run["video_id"])
        jobs = db.latest_jobs_for_run(database_path, selected_run["id"])
        job_rows = "".join(_job_row(row) for row in jobs)
        if job_rows:
            outputs += (
                "<section><h2>Jobs</h2><table>"
                "<thead><tr><th>Action</th><th>Status</th><th>Progress</th><th>Message</th></tr></thead>"
                f"<tbody>{job_rows}</tbody></table></section>"
            )

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
    label {{ display: grid; gap: 4px; font-weight: 600; }}
    textarea {{ width: 100%; min-height: 140px; }}
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
    .preview {{
      white-space: pre-wrap; max-height: 240px; overflow: auto; background: white;
      padding: 10px; border: 1px solid #d9dee2;
    }}
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
      <input type="hidden" name="csrf_token" value="{html.escape(csrf_token)}">
      <input type="hidden" name="action" value="create">
      <label>Video URL
        <input name="video_url" type="url" required placeholder="https://www.youtube.com/watch?v=...">
      </label>
      <label>Report language
        <input name="report_language" value="en">
      </label>
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


def _run_job(
    config: AppConfig,
    database_path: Path | str,
    run_id: int,
    action: str,
    form: dict[str, list[str]],
    job_id: int,
) -> None:
    db.update_job(database_path, job_id=job_id, status="running", progress=5, message="Running")
    try:
        output = _run_action(config, database_path, run_id, action, form)
    except Exception as exc:
        LOGGER.exception("Job failed: run=%s action=%s", run_id, action)
        db.update_job(
            database_path,
            job_id=job_id,
            status="failed",
            progress=100,
            message=_public_error(exc),
        )
        return
    db.update_job(
        database_path,
        job_id=job_id,
        status="succeeded",
        progress=100,
        message="Completed",
        output_path=str(output) if output else None,
    )


def _run_action(
    config: AppConfig,
    database_path: Path | str,
    run_id: int,
    action: str,
    form: dict[str, list[str]],
) -> Path | str | None:
    run = db.get_pipeline_run(database_path, run_id)
    if run is None:
        raise ValueError(f"Run not found: {run_id}")

    if action == "captions":
        extract_required_subtitles(database_path, run_id)
        return None
    elif action == "clean_transcript":
        return clean_run_transcript(database_path, run_id, outputs_path=config.paths.transcripts)
    elif action == "analysis":
        api_key = form.get("openai_api_key", [""])[0] or config.api_keys.openai
        client = OpenAIAnalysisClient(api_key=api_key)
        db.set_step_status(database_path, run_id=run_id, step="analysis", status="running")
        summary_id = analyze_cleaned_transcript(
            database_path,
            video_id=run["video_id"],
            client=client,
            max_chars=config.pipeline.analysis_max_chars,
        )
        db.set_step_status(
            database_path,
            run_id=run_id,
            step="analysis",
            status="succeeded",
            output_path=f"sqlite:summaries/{summary_id}",
        )
        db.set_run_status(database_path, run_id=run_id, status="running", current_step="brief")
        return f"sqlite:summaries/{summary_id}"
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
        return path
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
        return path
    else:
        raise ValueError(f"Unsupported action: {action}")


def _controls(run_id: int, next_step: str | None, *, csrf_token: str = "") -> str:
    if next_step is None:
        return ""
    secret = ""
    if next_step == "analysis":
        secret = (
            '<label>OpenAI API key'
            '<input name="openai_api_key" type="password" placeholder="OpenAI API key">'
            "</label>"
        )
    elif next_step == "source_verification":
        secret = (
            '<label>Semantic Scholar API key'
            '<input name="semantic_scholar_api_key" type="password" '
            'placeholder="Semantic Scholar API key"></label>'
            '<label>NCBI API key'
            '<input name="ncbi_api_key" type="password" placeholder="NCBI API key"></label>'
        )
    return f"""
    <form method="post">
      <input type="hidden" name="csrf_token" value="{html.escape(csrf_token)}">
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
    video = db.get_video(database_path, video_id)
    links = []
    if video is not None and video["url"]:
        links.append(
            '<li>Source video: '
            f'<a href="{html.escape(video["url"])}">{html.escape(video["title"])}</a></li>'
        )
    if cleaned is not None and cleaned["output_path"]:
        links.append(f"<li>Cleaned transcript: {html.escape(cleaned['output_path'])}</li>")
    if brief is not None:
        run = db.latest_pipeline_run_for_video(database_path, video_id)
        run_id = run["id"] if run is not None else ""
        links.append(
            f'<li>Markdown brief: <a href="/brief?run_id={run_id}">view</a> '
            f'<a href="/brief/download?run_id={run_id}">download</a></li>'
        )
    if verification is not None:
        links.append(
            "<li>"
            f"Source verification: {html.escape(verification['status'])} "
            f"({_verification_counts(database_path, verification['id'])})"
            "</li>"
        )
    preview = ""
    if cleaned is not None:
        preview_text = html.escape(cleaned["text"][:1200])
        preview = f"<h3>Cleaned transcript preview</h3><div class=\"preview\">{preview_text}</div>"
    if not links and not preview:
        return ""
    return f"<section><h2>Outputs</h2><ul>{''.join(links)}</ul>{preview}</section>"


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


def _job_row(row) -> str:
    return (
        "<tr>"
        f"<td>{html.escape(row['action'].replace('_', ' '))}</td>"
        f"<td class=\"status\">{html.escape(row['status'])}</td>"
        f"<td>{int(row['progress'])}%</td>"
        f"<td>{html.escape(row['message'] or '')}</td>"
        "</tr>"
    )


def _int_value(value: str) -> int | None:
    try:
        return int(value)
    except ValueError:
        return None


def render_brief_page(
    database_path: Path | str,
    briefs_path: Path | str,
    *,
    run_id: int | None,
) -> str:
    path = _brief_path_for_run(database_path, briefs_path, run_id)
    if path is None:
        content = "<p class=\"notice\">No report is available for this run.</p>"
    else:
        content = _markdown_to_html(path.read_text(encoding="utf-8"))
    return f"""<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>ClaimLens Report</title></head>
<body><main>{content}</main></body></html>"""


def _brief_path_for_run(
    database_path: Path | str,
    briefs_path: Path | str,
    run_id: int | None,
) -> Path | None:
    if run_id is None:
        return None
    run = db.get_pipeline_run(database_path, run_id)
    if run is None or not run["video_id"]:
        return None
    artifact = db.latest_brief_artifact(database_path, run["video_id"])
    if artifact is None:
        return None
    root = Path(briefs_path).resolve()
    path = Path(artifact["path"]).resolve()
    try:
        path.relative_to(root)
    except ValueError:
        return None
    return path if path.exists() else None


def _markdown_to_html(markdown: str) -> str:
    lines = []
    in_list = False
    for raw in markdown.splitlines():
        line = raw.strip()
        if not line:
            if in_list:
                lines.append("</ul>")
                in_list = False
            continue
        if line.startswith("#"):
            if in_list:
                lines.append("</ul>")
                in_list = False
            level = min(6, len(line) - len(line.lstrip("#")))
            text = html.escape(line[level:].strip())
            lines.append(f"<h{level}>{text}</h{level}>")
        elif line.startswith("- "):
            if not in_list:
                lines.append("<ul>")
                in_list = True
            lines.append(f"<li>{html.escape(line[2:])}</li>")
        else:
            if in_list:
                lines.append("</ul>")
                in_list = False
            lines.append(f"<p>{html.escape(line)}</p>")
    if in_list:
        lines.append("</ul>")
    return "\n".join(lines)


def _check_rate_limit(client: str, config: AppConfig) -> None:
    now = time.monotonic()
    window = config.web.rate_limit_window_seconds
    events = [stamp for stamp in RATE_LIMITS.get(client, []) if now - stamp < window]
    if len(events) >= config.web.rate_limit_actions:
        raise ValueError("Too many actions submitted recently. Wait and try again.")
    events.append(now)
    RATE_LIMITS[client] = events


def _public_error(exc: Exception) -> str:
    text = str(exc).strip()
    if not text:
        return "The action failed."
    if "/" in text or "\\" in text:
        return "The action failed. Check the application logs for details."
    return text
