"""Local HTML process page for one-video runs."""

from __future__ import annotations

import html
import logging
import secrets
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from claimlens import db
from claimlens.analysis import OpenAIAnalysisClient, analyze_cleaned_transcript
from claimlens.api_keys import KeyContext, resolve_api_key, save_user_api_key
from claimlens.auth import (
    hash_password,
    new_guest_token,
    new_session_token,
    token_digest,
    verify_password,
)
from claimlens.briefs import generate_brief, generate_verified_brief
from claimlens.config import AppConfig
from claimlens.kapsule_auth import authenticate as authenticate_kapsule_account
from claimlens.pipeline import (
    add_manual_transcript,
    clean_run_transcript,
    create_run,
    extract_required_subtitles,
    next_eligible_step,
)
from claimlens.verification import default_adapters, verify_sources

LOGGER = logging.getLogger(__name__)
EXECUTOR = ThreadPoolExecutor(max_workers=2, thread_name_prefix="claimlens-job")
RATE_LIMITS: dict[str, list[float]] = {}


@dataclass(frozen=True)
class WebContext:
    user_id: int | None
    email: str | None
    csrf_token: str
    guest_token: str
    session_token: str | None


def serve_process_page(config: AppConfig, *, host: str, port: int) -> None:
    database_path = config.paths.database
    db.init_db(database_path)
    guest_csrf_token = secrets.token_urlsafe(32)

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            query = parse_qs(parsed.query)
            run_id = _int_value(query.get("run_id", [""])[0])
            context = self._context()
            if parsed.path == "/health":
                self._send_text("ok\n")
                return
            if parsed.path == "/login":
                self._send_html(render_login_page(context=context))
                return
            if parsed.path == "/options":
                self._send_html(
                    render_options_page(database_path, config, context=context),
                    status=200 if context.user_id is not None else 403,
                )
                return
            if parsed.path == "/brief":
                self._send_html(
                    render_brief_page(
                        database_path,
                        config.paths.briefs,
                        run_id=run_id,
                        user_id=context.user_id,
                        guest_token=context.guest_token,
                        context=context,
                    )
                )
                return
            if parsed.path == "/brief/download":
                self._send_brief_download(
                    database_path,
                    config.paths.briefs,
                    run_id=run_id,
                    user_id=context.user_id,
                    guest_token=context.guest_token,
                )
                return
            body = render_process_page(
                database_path,
                run_id=run_id,
                csrf_token=context.csrf_token,
                user_id=context.user_id,
                guest_token=context.guest_token,
                context=context,
            )
            self._send_html(body)

        def do_POST(self) -> None:  # noqa: N802
            context = self._context()
            try:
                form = self._read_form()
            except ValueError as exc:
                body = render_process_page(
                    database_path,
                    notice=str(exc),
                    csrf_token=context.csrf_token,
                    user_id=context.user_id,
                    guest_token=context.guest_token,
                    context=context,
                )
                self._send_html(body, status=400)
                return
            if form.get("csrf_token", [""])[0] != context.csrf_token:
                body = render_process_page(
                    database_path,
                    notice="The form expired. Reload the page and try again.",
                    csrf_token=context.csrf_token,
                    user_id=context.user_id,
                    guest_token=context.guest_token,
                    context=context,
                )
                self._send_html(body, status=403)
                return
            action = form.get("action", [""])[0]
            run_id: int | None = None
            try:
                _check_rate_limit(self.client_address[0], config)
                if action == "login":
                    self._handle_login(form)
                    return
                if action == "register":
                    self._handle_register(form)
                    return
                if action == "logout":
                    self._handle_logout(context)
                    return
                if action in {"save_api_key", "delete_api_key", "test_api_key"}:
                    self._handle_options_action(form, context)
                    return
                if action == "create":
                    run_id = create_run(
                        database_path,
                        form.get("video_url", [""])[0],
                        report_language=form.get(
                            "report_language",
                            [config.pipeline.report_language],
                        )[0],
                        fetch_metadata=True,
                        user_id=context.user_id,
                        guest_token=None if context.user_id is not None else context.guest_token,
                    )
                else:
                    run_id = int(form.get("run_id", [""])[0])
                    run = db.get_visible_pipeline_run(
                        database_path,
                        run_id,
                        user_id=context.user_id,
                        guest_token=context.guest_token,
                    )
                    if run is None:
                        raise ValueError("Run not found.")
                    job_id = db.create_job(database_path, run_id=run_id, action=action)
                    if job_id is None:
                        raise ValueError("This action is already queued or running for the run.")
                    EXECUTOR.submit(
                        _run_job,
                        config,
                        database_path,
                        run_id,
                        action,
                        form,
                        job_id,
                        context.user_id,
                        context.guest_token,
                    )
            except Exception as exc:
                LOGGER.info("Web action rejected: %s", exc)
                body = render_process_page(
                    database_path,
                    run_id=run_id,
                    notice=_public_error(exc),
                    csrf_token=context.csrf_token,
                    user_id=context.user_id,
                    guest_token=context.guest_token,
                    context=context,
                )
                self._send_html(body, status=400)
                return

            self.send_response(303)
            self.send_header("Location", f"/?run_id={run_id}")
            if not self._cookie("claimlens_guest"):
                self._set_cookie("claimlens_guest", context.guest_token, config=config)
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

        def _send_text(self, body: str, *, status: int = 200) -> None:
            encoded = body.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def _send_brief_download(
            self,
            database_path: Path | str,
            briefs_path: Path | str,
            *,
            run_id: int | None,
            user_id: int | None,
            guest_token: str | None,
        ) -> None:
            path = _brief_path_for_run(
                database_path,
                briefs_path,
                run_id,
                user_id=user_id,
                guest_token=guest_token,
            )
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

        def _context(self) -> WebContext:
            session_token = self._cookie("claimlens_session")
            guest_token = self._cookie("claimlens_guest") or new_guest_token()
            if session_token:
                session = db.get_session(database_path, token_digest(session_token))
                if session is not None:
                    return WebContext(
                        user_id=int(session["user_id"]),
                        email=session["email"],
                        csrf_token=session["csrf_token"],
                        guest_token=guest_token,
                        session_token=session_token,
                    )
            return WebContext(
                user_id=None,
                email=None,
                csrf_token=guest_csrf_token,
                guest_token=guest_token,
                session_token=None,
            )

        def _handle_login(self, form: dict[str, list[str]]) -> None:
            email = form.get("email", [""])[0]
            password = form.get("password", [""])[0]
            user = db.get_user_by_email(database_path, email)
            if user is not None and verify_password(password, user["password_hash"]):
                self._create_login_session(int(user["id"]))
                return

            kapsule_account = authenticate_kapsule_account(
                config.web.kapsule_database,
                email,
                password,
            )
            if kapsule_account is not None:
                user_id = db.get_or_create_user(
                    database_path,
                    email=kapsule_account.email,
                    password_hash=f"kapsule:{kapsule_account.id}",
                    display_name=kapsule_account.email,
                )
                self._create_login_session(user_id)
                return

            if user is None or not verify_password(password, user["password_hash"]):
                self._send_html(
                    render_login_page(
                        context=WebContext(
                            user_id=None,
                            email=None,
                            csrf_token=guest_csrf_token,
                            guest_token=self._cookie("claimlens_guest") or new_guest_token(),
                            session_token=None,
                        ),
                        notice="Invalid email or password.",
                    ),
                    status=403,
                )
                return

        def _handle_register(self, form: dict[str, list[str]]) -> None:
            if not config.web.registration_enabled and db.user_count(database_path) > 0:
                raise ValueError("Registration is closed.")
            email = form.get("email", [""])[0]
            password = form.get("password", [""])[0]
            user_id = db.create_user(
                database_path,
                email=email,
                password_hash=hash_password(password),
                display_name=email,
            )
            self._create_login_session(user_id)

        def _create_login_session(self, user_id: int) -> None:
            token = new_session_token()
            csrf = secrets.token_urlsafe(32)
            expires_at = (datetime.now(UTC) + timedelta(days=14)).strftime("%Y-%m-%d %H:%M:%S")
            db.create_session(
                database_path,
                user_id=user_id,
                token_hash=token_digest(token),
                csrf_token=csrf,
                expires_at=expires_at,
            )
            self.send_response(303)
            self.send_header("Location", "/")
            self._set_cookie("claimlens_session", token, config=config)
            self.end_headers()

        def _handle_logout(self, context: WebContext) -> None:
            if context.session_token:
                db.delete_session(database_path, token_digest(context.session_token))
            self.send_response(303)
            self.send_header("Location", "/")
            self._clear_cookie("claimlens_session", config=config)
            self.end_headers()

        def _handle_options_action(
            self,
            form: dict[str, list[str]],
            context: WebContext,
        ) -> None:
            if context.user_id is None:
                raise ValueError("Login is required.")
            provider = form.get("provider", [""])[0]
            if form.get("action", [""])[0] == "delete_api_key":
                db.delete_user_api_key(database_path, user_id=context.user_id, provider=provider)
            elif form.get("action", [""])[0] == "test_api_key":
                key = resolve_api_key(
                    database_path,
                    config,
                    provider=provider,
                    context=KeyContext(user_id=context.user_id, request_keys={}),
                )
                if not key:
                    raise ValueError("No saved key to test.")
                db.mark_user_api_key_tested(
                    database_path,
                    user_id=context.user_id,
                    provider=provider,
                )
            else:
                save_user_api_key(
                    database_path,
                    user_id=context.user_id,
                    provider=provider,
                    value=form.get("api_key", [""])[0],
                    deployment_secret=config.web.key_encryption_secret,
                )
            self.send_response(303)
            self.send_header("Location", "/options")
            self.end_headers()

        def _cookie(self, name: str) -> str | None:
            raw = self.headers.get("Cookie", "")
            for part in raw.split(";"):
                key, _, value = part.strip().partition("=")
                if key == name:
                    return value or None
            return None

        def _set_cookie(self, name: str, value: str, *, config: AppConfig) -> None:
            secure = "; Secure" if config.web.secure_cookies else ""
            self.send_header(
                "Set-Cookie",
                f"{name}={value}; HttpOnly; SameSite=Lax; Path=/{secure}",
            )

        def _clear_cookie(self, name: str, *, config: AppConfig) -> None:
            secure = "; Secure" if config.web.secure_cookies else ""
            self.send_header(
                "Set-Cookie",
                f"{name}=; Max-Age=0; HttpOnly; SameSite=Lax; Path=/{secure}",
            )

    server = ThreadingHTTPServer((host, port), Handler)
    print(f"ClaimLens process page: http://{host}:{port}")
    server.serve_forever()


def render_process_page(
    database_path: Path | str,
    *,
    run_id: int | None = None,
    notice: str | None = None,
    csrf_token: str = "",
    user_id: int | None = None,
    guest_token: str | None = None,
    context: WebContext | None = None,
) -> str:
    selected_run = (
        db.get_visible_pipeline_run(
            database_path,
            run_id,
            user_id=user_id,
            guest_token=guest_token,
        )
        if run_id and (user_id is not None or guest_token)
        else db.get_pipeline_run(database_path, run_id)
        if run_id
        else None
    )
    runs = (
        db.list_visible_pipeline_runs(database_path, user_id=user_id, guest_token=guest_token)
        if user_id is not None or guest_token
        else db.list_pipeline_runs(database_path)
    )
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
    nav {{ display: flex; gap: 16px; justify-content: space-between; align-items: center;
      padding: 12px 28px; background: #172026; color: white; }}
    nav a, nav button {{ color: white; background: transparent; border: 0; padding: 0; }}
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
{_nav(context, csrf_token)}
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
    {_manual_transcript_form(selected_run["id"], csrf_token) if selected_run is not None else ""}
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
    user_id: int | None = None,
    guest_token: str | None = None,
) -> None:
    db.update_job(database_path, job_id=job_id, status="running", progress=5, message="Running")
    try:
        output = _run_action(
            config,
            database_path,
            run_id,
            action,
            form,
            user_id=user_id,
            guest_token=guest_token,
        )
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
    user_id: int | None = None,
    guest_token: str | None = None,
) -> Path | str | None:
    run = db.get_pipeline_run(database_path, run_id)
    if run is None:
        raise ValueError(f"Run not found: {run_id}")

    if action == "captions":
        extract_required_subtitles(database_path, run_id)
        return None
    elif action == "manual_transcript":
        transcript_id = add_manual_transcript(
            database_path,
            run_id,
            text=form.get("transcript_text", [""])[0],
            language=form.get("transcript_language", ["unknown"])[0],
            user_id=user_id,
            guest_token=guest_token,
        )
        return f"sqlite:transcripts/{transcript_id}"
    elif action == "clean_transcript":
        return clean_run_transcript(database_path, run_id, outputs_path=config.paths.transcripts)
    elif action == "analysis":
        api_key = resolve_api_key(
            database_path,
            config,
            provider="openai",
            context=KeyContext(
                user_id=user_id,
                request_keys={"openai": form.get("openai_api_key", [""])[0]},
            ),
        )
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
        semantic_key = resolve_api_key(
            database_path,
            config,
            provider="semantic_scholar",
            context=KeyContext(
                user_id=user_id,
                request_keys={
                    "semantic_scholar": form.get("semantic_scholar_api_key", [""])[0]
                },
            ),
        )
        ncbi_key = resolve_api_key(
            database_path,
            config,
            provider="ncbi",
            context=KeyContext(
                user_id=user_id,
                request_keys={"ncbi": form.get("ncbi_api_key", [""])[0]},
            ),
        )
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


def _manual_transcript_form(run_id: int, csrf_token: str) -> str:
    return f"""
    <form method="post">
      <input type="hidden" name="csrf_token" value="{html.escape(csrf_token)}">
      <input type="hidden" name="run_id" value="{run_id}">
      <input type="hidden" name="action" value="manual_transcript">
      <label>Transcript language
        <input name="transcript_language" value="unknown">
      </label>
      <label>Paste transcript fallback
        <textarea name="transcript_text"
          placeholder="Paste .txt, .srt, or .vtt text here"></textarea>
      </label>
      <button type="submit">Use pasted transcript</button>
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


def _nav(context: WebContext | None, csrf_token: str) -> str:
    if context is not None and context.user_id is not None:
        auth = (
            f"<span>{html.escape(context.email or '')}</span>"
            '<a href="/options">Options</a>'
            '<form method="post" style="display:inline">'
            f'<input type="hidden" name="csrf_token" value="{html.escape(csrf_token)}">'
            '<input type="hidden" name="action" value="logout">'
            '<button type="submit">Logout</button></form>'
        )
    else:
        auth = '<a href="/login">Login</a>'
    return f"<nav><a href=\"/\">ClaimLens</a><div>{auth}</div></nav>"


def render_login_page(*, context: WebContext, notice: str | None = None) -> str:
    notice_html = f'<p class="notice">{html.escape(notice)}</p>' if notice else ""
    csrf = html.escape(context.csrf_token)
    return f"""<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>ClaimLens Login</title></head>
<body>
{_nav(context, context.csrf_token)}
<main>
  <h1>Login</h1>
  {notice_html}
  <form method="post">
    <input type="hidden" name="csrf_token" value="{csrf}">
    <input type="hidden" name="action" value="login">
    <label>Email <input name="email" type="email" required></label>
    <label>Password <input name="password" type="password" required></label>
    <button type="submit">Login</button>
  </form>
  <h2>Create first account</h2>
  <form method="post">
    <input type="hidden" name="csrf_token" value="{csrf}">
    <input type="hidden" name="action" value="register">
    <label>Email <input name="email" type="email" required></label>
    <label>Password <input name="password" type="password" required></label>
    <button type="submit">Create account</button>
  </form>
</main>
</body></html>"""


def render_options_page(
    database_path: Path | str,
    config: AppConfig,
    *,
    context: WebContext,
) -> str:
    if context.user_id is None:
        return """<!doctype html><html lang="en"><body><main>
<p class="notice">Login is required.</p></main></body></html>"""
    rows = db.list_user_api_keys(database_path, user_id=context.user_id)
    status = {row["provider"]: row for row in rows}
    sections = []
    for provider, label in [
        ("openai", "OpenAI"),
        ("semantic_scholar", "Semantic Scholar"),
        ("ncbi", "NCBI / PubMed"),
    ]:
        row = status.get(provider)
        saved = (
            f"Saved: {html.escape(row['masked_value'])}, updated {html.escape(row['updated_at'])}"
            + (
                f", tested {html.escape(row['tested_at'])}"
                if row and row["tested_at"]
                else ""
            )
            if row
            else "No saved key."
        )
        sections.append(
            f"""
            <section>
              <h2>{label}</h2>
              <p>{saved}</p>
              <form method="post">
                <input type="hidden" name="csrf_token" value="{html.escape(context.csrf_token)}">
                <input type="hidden" name="action" value="save_api_key">
                <input type="hidden" name="provider" value="{provider}">
                <label>API key <input name="api_key" type="password" required></label>
                <button type="submit">Save key</button>
              </form>
              <form method="post">
                <input type="hidden" name="csrf_token" value="{html.escape(context.csrf_token)}">
                <input type="hidden" name="action" value="test_api_key">
                <input type="hidden" name="provider" value="{provider}">
                <button type="submit">Test saved key</button>
              </form>
              <form method="post">
                <input type="hidden" name="csrf_token" value="{html.escape(context.csrf_token)}">
                <input type="hidden" name="action" value="delete_api_key">
                <input type="hidden" name="provider" value="{provider}">
                <button type="submit">Delete key</button>
              </form>
            </section>
            """
        )
    secret_notice = (
        ""
        if config.web.key_encryption_secret
        else "<p class=\"notice\">Set CLAIMLENS_KEY_ENCRYPTION_SECRET before saving keys.</p>"
    )
    return f"""<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>ClaimLens Options</title></head>
<body>{_nav(context, context.csrf_token)}<main>
<h1>Options</h1>
{secret_notice}
{''.join(sections)}
</main></body></html>"""


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
    user_id: int | None = None,
    guest_token: str | None = None,
    context: WebContext | None = None,
) -> str:
    path = _brief_path_for_run(
        database_path,
        briefs_path,
        run_id,
        user_id=user_id,
        guest_token=guest_token,
    )
    if path is None:
        content = "<p class=\"notice\">No report is available for this run.</p>"
    else:
        content = _markdown_to_html(path.read_text(encoding="utf-8"))
    return f"""<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>ClaimLens Report</title></head>
<body>{_nav(context, context.csrf_token) if context else ''}<main>{content}</main></body></html>"""


def _brief_path_for_run(
    database_path: Path | str,
    briefs_path: Path | str,
    run_id: int | None,
    user_id: int | None = None,
    guest_token: str | None = None,
) -> Path | None:
    if run_id is None:
        return None
    run = (
        db.get_visible_pipeline_run(
            database_path,
            run_id,
            user_id=user_id,
            guest_token=guest_token,
        )
        if user_id is not None or guest_token
        else db.get_pipeline_run(database_path, run_id)
    )
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
