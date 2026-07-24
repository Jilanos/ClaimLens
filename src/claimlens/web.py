"""Local HTML process page for one-video runs."""

from __future__ import annotations

import html
import json
import logging
import secrets
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from claimlens import db
from claimlens.analysis import OpenAIAnalysisClient, analyze_cleaned_transcript
from claimlens.api_keys import KeyContext, resolve_api_key, save_supadata_api_key, save_user_api_key
from claimlens.auth import (
    hash_password,
    new_guest_token,
    new_session_token,
    token_digest,
    verify_password,
)
from claimlens.briefs import generate_brief, generate_verified_brief
from claimlens.config import AppConfig, SourceConfig
from claimlens.kapsule_auth import authenticate as authenticate_kapsule_account
from claimlens.pipeline import (
    add_manual_transcript,
    clean_run_transcript,
    create_run,
    extract_required_subtitles,
    next_eligible_step,
)
from claimlens.verification import default_adapters, verify_sources
from claimlens.youtube import SupadataClient, SupadataError

LOGGER = logging.getLogger(__name__)
EXECUTOR = ThreadPoolExecutor(max_workers=2, thread_name_prefix="claimlens-job")
STEP_LABELS = {
    "captions": "Get captions",
    "clean_transcript": "Prepare transcript",
    "analysis": "Analyze claims",
    "brief": "Create brief",
    "source_verification": "Check sources",
}
STATUS_LABELS = {
    "queued": "Queued",
    "running": "In progress",
    "succeeded": "Complete",
    "completed_with_warnings": "Complete with limits",
    "failed": "Needs attention",
    "interrupted": "Interrupted",
    "pending": "Waiting",
}

LOGO_MARK = (
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" '
    'stroke-linecap="round" stroke-linejoin="round"><circle cx="10.5" cy="10.5" r="6.5"/>'
    '<path d="m21 21-5.2-5.2"/><path d="M8 10.5h5M10.5 8v5" stroke-width="1.8"/></svg>'
)

STYLES = """
:root {
  --ink:#12181d; --ink-2:#38454e; --muted:#6a7a84;
  --line:#e2e7eb; --line-2:#eef1f3; --surface:#fff; --surface-2:#f7f9fa; --ground:#eef2f4;
  --accent:#0b7d8c; --accent-2:#0a6270; --accent-wash:#e2f2f4;
  --ok:#1f8a53; --ok-wash:#e4f4ea; --warn:#a86a12; --warn-wash:#f8efdd;
  --bad:#bd4126; --bad-wash:#f8e6df; --run:#2660d6; --run-wash:#e5edfb;
  --radius:12px; --radius-sm:8px;
  --shadow:0 1px 2px rgba(18,24,29,.04), 0 6px 20px rgba(18,24,29,.06);
  --shadow-sm:0 1px 2px rgba(18,24,29,.06);
  --sans:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  --mono:ui-monospace,"SF Mono","JetBrains Mono",Menlo,Consolas,monospace;
}
@media (prefers-color-scheme: dark) {
  :root {
    --ink:#e7edf1; --ink-2:#aeb9c1; --muted:#7c8b94;
    --line:#26313a; --line-2:#1e272e; --surface:#151d24; --surface-2:#111820; --ground:#0c1218;
    --accent:#2ba7b6; --accent-2:#39b8c7; --accent-wash:#12303540;
    --ok:#43b877; --ok-wash:#12291d; --warn:#d59a3f; --warn-wash:#2a2113;
    --bad:#e26b4d; --bad-wash:#2c1712; --run:#5b8bf0; --run-wash:#141f34;
    --shadow:0 1px 2px rgba(0,0,0,.3), 0 8px 26px rgba(0,0,0,.35);
    --shadow-sm:0 1px 2px rgba(0,0,0,.35);
  }
}
* { box-sizing:border-box; }
body { margin:0; background:var(--ground); color:var(--ink); font-family:var(--sans);
  line-height:1.5; font-size:15px; -webkit-font-smoothing:antialiased; }
h1,h2,h3 { margin:0; text-wrap:balance; letter-spacing:-.01em; }
a { color:var(--accent-2); }
nav.app { display:flex; align-items:center; justify-content:space-between; gap:16px;
  padding:0 24px; height:60px; background:var(--surface); border-bottom:1px solid var(--line);
  position:sticky; top:0; z-index:20; }
.brand { display:flex; align-items:center; gap:10px; font-weight:700; font-size:17px;
  letter-spacing:-.02em; color:var(--ink); text-decoration:none; }
.brand .mark { width:30px; height:30px; border-radius:9px; display:grid; place-items:center;
  background:linear-gradient(150deg,var(--accent),var(--accent-2)); color:#fff; flex:none; }
.brand .mark svg { width:17px; height:17px; }
.navlinks { display:flex; align-items:center; gap:6px; }
.navlinks a { color:var(--ink-2); text-decoration:none; font-weight:500; font-size:14px;
  padding:7px 12px; border-radius:8px; }
.navlinks a:hover { background:var(--surface-2); color:var(--ink); }
.navlinks a.active { color:var(--accent-2); background:var(--accent-wash); }
.navuser { display:flex; align-items:center; gap:12px; }
.navuser .who { font-size:13px; color:var(--muted); }
.avatar { width:30px; height:30px; border-radius:50%; background:var(--accent-wash);
  color:var(--accent-2); display:grid; place-items:center; font-weight:700; font-size:13px; }
main { max-width:1000px; margin:0 auto; padding:34px 24px 80px; }
.page-head { margin-bottom:24px; }
.page-head h1 { font-size:26px; }
.page-head p { color:var(--muted); margin:6px 0 0; max-width:62ch; }
.card { background:var(--surface); border:1px solid var(--line); border-radius:var(--radius);
  box-shadow:var(--shadow); }
.card + .card { margin-top:20px; }
.card-head { display:flex; align-items:center; justify-content:space-between; gap:12px;
  padding:16px 20px; border-bottom:1px solid var(--line-2); }
.card-head h2 { font-size:15px; }
.card-head .sub { font-size:12px; color:var(--muted); }
.card-body { padding:20px; }
.field { display:grid; gap:6px; }
.field > span { font-size:13px; font-weight:600; color:var(--ink-2); }
.check { display:inline-flex; align-items:center; gap:8px; font-size:13px; color:var(--ink-2); }
.check input { width:auto; min-height:0; }
input, select, textarea { font:inherit; color:var(--ink); background:var(--surface); width:100%;
  border:1px solid var(--line); border-radius:var(--radius-sm); padding:9px 11px; min-height:40px;
  transition:border-color .12s, box-shadow .12s; }
input::placeholder, textarea::placeholder { color:var(--muted); }
input:focus, select:focus, textarea:focus { outline:none; border-color:var(--accent);
  box-shadow:0 0 0 3px var(--accent-wash); }
textarea { min-height:120px; resize:vertical; font-family:var(--mono); font-size:13px; }
.btn { display:inline-flex; align-items:center; gap:8px; justify-content:center; font:inherit;
  font-weight:600; font-size:14px; cursor:pointer; padding:9px 16px; min-height:40px;
  border-radius:var(--radius-sm); border:1px solid transparent; white-space:nowrap;
  transition:filter .12s, background .12s; }
.btn-primary { background:var(--accent); color:#fff; }
.btn-primary:hover { filter:brightness(1.06); }
.btn-ghost { background:var(--surface); color:var(--ink); border-color:var(--line); }
.btn-ghost:hover { background:var(--surface-2); }
.btn-danger { background:transparent; color:var(--bad);
  border-color:color-mix(in srgb, var(--bad) 40%, transparent); }
.btn-danger:hover { background:var(--bad-wash); }
.btn:focus-visible { outline:2px solid var(--accent); outline-offset:2px; }
.btn-sm { min-height:34px; padding:6px 12px; font-size:13px; }
.badge { display:inline-flex; align-items:center; gap:6px; font-size:12px; font-weight:600;
  padding:3px 9px; border-radius:999px; text-transform:capitalize; }
.badge::before { content:""; width:6px; height:6px; border-radius:50%; background:currentColor; }
.badge.ok { color:var(--ok); background:var(--ok-wash); }
.badge.run { color:var(--run); background:var(--run-wash); }
.badge.warn { color:var(--warn); background:var(--warn-wash); }
.badge.bad { color:var(--bad); background:var(--bad-wash); }
.badge.idle { color:var(--muted); background:var(--surface-2); }
.stepper { display:grid; grid-template-columns:repeat(5,1fr); }
.step { position:relative; padding:16px 14px; }
.step:not(:last-child)::after { content:""; position:absolute; top:29px; right:-1px;
  width:calc(100% - 28px);
  height:1px; background:var(--line-2); }
.step .dot { width:26px; height:26px; border-radius:50%; display:grid; place-items:center;
  font-size:12px; font-weight:700; margin-bottom:10px; border:2px solid var(--line);
  color:var(--muted); background:var(--surface); }
.step.done .dot { background:var(--ok); border-color:var(--ok); color:#fff; }
.step.active .dot { background:var(--run); border-color:var(--run); color:#fff;
  box-shadow:0 0 0 4px var(--run-wash); }
.step.bad .dot { background:var(--bad); border-color:var(--bad); color:#fff; }
.step .name { font-weight:600; font-size:13.5px; text-transform:capitalize; }
.step .meta { font-size:12px; color:var(--muted); margin-top:3px; }
table { width:100%; border-collapse:collapse; font-size:14px; background:transparent; }
th { text-align:left; font-size:11px; letter-spacing:.06em; text-transform:uppercase;
  color:var(--muted); font-weight:700; padding:10px 14px; border-bottom:1px solid var(--line); }
td { padding:12px 14px; border-bottom:1px solid var(--line-2); vertical-align:middle; }
tr:last-child td { border-bottom:0; }
.status { font-weight:600; }
.row { display:flex; gap:12px; align-items:flex-end; flex-wrap:wrap; }
.row .field { flex:1 1 240px; }
.grow { flex:1; }
.notice { display:flex; gap:10px; align-items:flex-start; padding:12px 14px;
  border-radius:var(--radius-sm); font-size:13.5px; border:1px solid; margin:0 0 20px;
  color:var(--bad); background:var(--bad-wash);
  border-color:color-mix(in srgb, var(--bad) 25%, transparent); }
.preview { white-space:pre-wrap; max-height:240px; overflow:auto; font-family:var(--mono);
  font-size:12.5px; color:var(--ink-2); background:var(--surface-2); border:1px solid var(--line-2);
  border-radius:var(--radius-sm); padding:14px; }
ul.out { list-style:none; padding:0; margin:0; }
ul.out li { padding:11px 4px; border-bottom:1px solid var(--line-2); font-size:14px; }
ul.out li:last-child { border-bottom:0; }
.auth-wrap { min-height:calc(100vh - 60px); display:grid; place-items:center; padding:40px 20px; }
.auth-card { width:100%; max-width:420px; }
.auth-card .card-body { padding:28px; display:grid; gap:16px; }
.auth-logo { display:grid; place-items:center; gap:12px; text-align:center; margin-bottom:4px; }
.auth-logo .mark { width:46px; height:46px; border-radius:13px; display:grid; place-items:center;
  background:linear-gradient(150deg,var(--accent),var(--accent-2)); color:#fff; }
.auth-logo .mark svg { width:25px; height:25px; }
.auth-logo h1 { font-size:20px; }
.divider { display:flex; align-items:center; gap:12px; color:var(--muted); font-size:12px; }
.divider::before, .divider::after { content:""; height:1px; background:var(--line); flex:1; }
.report { max-width:760px; margin:0 auto; }
.report .card-body { padding:34px 40px; }
.report h1 { font-size:24px; }
.report h2 { font-size:17px; margin:24px 0 10px; padding-bottom:6px;
  border-bottom:1px solid var(--line-2); }
.report h3 { font-size:15px; margin:18px 0 8px; }
.report p { color:var(--ink-2); margin:0 0 12px; }
.report ul { margin:0 0 14px; padding-left:20px; color:var(--ink-2); }
.report li { margin:5px 0; }
.mono { font-family:var(--mono); font-size:12.5px; color:var(--muted); }
.workspace { display:grid; grid-template-columns:minmax(0,1fr) minmax(240px,320px); gap:24px;
  align-items:start; }
.workspace-main { min-width:0; }
.workspace-side { display:grid; gap:12px; }
.workspace-title { display:flex; align-items:center; gap:10px; flex-wrap:wrap; }
.workspace-title h2 { font-size:18px; }
.workspace-url { margin:5px 0 0; color:var(--muted); font-size:13px; overflow-wrap:anywhere; }
.workspace-action { background:var(--accent-wash);
  border:1px solid color-mix(in srgb,var(--accent) 22%,transparent);
  border-radius:var(--radius-sm); padding:16px; }
.workspace-action h3 { font-size:14px; margin:0 0 4px; }
.workspace-action p { color:var(--ink-2); margin:0 0 12px; font-size:13.5px; }
.summary-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:10px; }
.summary-item { background:var(--surface-2); border:1px solid var(--line-2);
  border-radius:var(--radius-sm); padding:12px; }
.summary-item strong { display:block; font-size:19px; line-height:1.2; }
.summary-item span { display:block; margin-top:3px; color:var(--muted); font-size:12px; }
.history-list { display:grid; gap:8px; }
.history-row { display:flex; align-items:center; justify-content:space-between; gap:12px;
  padding:12px 4px;
  border-bottom:1px solid var(--line-2); }
.history-row:last-child { border-bottom:0; }
.history-row a { font-weight:600; text-decoration:none; }
.history-row small { display:block; color:var(--muted); margin-top:3px; }
.history-filter { max-width:170px; min-height:34px; padding:6px 9px; font-size:13px; }
.diagnostic { margin-top:16px; border-top:1px solid var(--line-2); padding-top:14px; }
.diagnostic summary { cursor:pointer; color:var(--ink-2); font-weight:600; font-size:13px; }
.diagnostic-body { margin-top:12px; overflow-x:auto; }
.table-wrap { overflow-x:auto; }
.sr-only { position:absolute; width:1px; height:1px; padding:0; margin:-1px; overflow:hidden;
  clip:rect(0,0,0,0); white-space:nowrap; border:0; }
.recovery { border-color:color-mix(in srgb,var(--warn) 30%,transparent); color:var(--ink-2);
  background:var(--warn-wash); }
.recovery-panel { margin-top:16px; padding-top:14px;
  border-top:1px solid color-mix(in srgb,var(--warn) 26%,transparent); }
.recovery-panel h4 { margin:0 0 4px; font-size:14px; }
.recovery-panel p { margin:0; color:var(--ink-2); font-size:13px; }
@media (max-width:720px) {
  .workspace { grid-template-columns:1fr; gap:16px; }
  .workspace-side { order:-1; }
  .stepper { grid-template-columns:1fr; }
  .step { padding:12px 14px 12px 42px; min-height:56px; }
  .step:not(:last-child)::after { top:42px; left:26px; right:auto; width:2px;
    height:calc(100% - 18px); }
  .step .dot { position:absolute; left:14px; top:12px; margin:0; }
  .summary-grid { grid-template-columns:1fr 1fr 1fr; gap:6px; }
  .summary-item { padding:9px; }
  .summary-item strong { font-size:16px; }
  .report .card-body { padding:24px; }
  .navuser .who { display:none; }
}
@media (prefers-reduced-motion: reduce) { * { transition:none !important; } }
"""


def _badge_class(status: str) -> str:
    return {
        "succeeded": "ok",
        "completed": "ok",
        "ready": "ok",
        "native": "ok",
        "running": "run",
        "saved": "warn",
        "exhausted": "warn",
        "completed_with_warnings": "warn",
        "warning": "warn",
        "rate_limited": "warn",
        "no_candidates": "warn",
        "interrupted": "warn",
        "failed": "bad",
        "invalid": "bad",
    }.get((status or "").lower(), "idle")


def _status_badge(status: str, *, suffix: str = "") -> str:
    label = html.escape(_status_label(status)) + suffix
    return f'<span class="badge {_badge_class(status)}">{label}</span>'


def _status_label(status: str | None) -> str:
    normalized = (status or "").lower()
    return STATUS_LABELS.get(normalized, normalized.replace("_", " ").title() or "Unknown")


def _step_label(step: str | None) -> str:
    normalized = (step or "").lower()
    return STEP_LABELS.get(normalized, normalized.replace("_", " ").title() or "Step")


def _int_form(form: dict[str, list[str]], name: str, default: int) -> int:
    try:
        return int(form.get(name, [str(default)])[0])
    except (TypeError, ValueError):
        return default


def _page_shell(
    title: str,
    body: str,
    *,
    context: WebContext | None,
    csrf_token: str = "",
    active: str | None = None,
    nav: bool = True,
) -> str:
    nav_html = _nav(context, csrf_token, active=active) if nav else ""
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <style>{STYLES}</style>
</head>
<body>
{nav_html}
{body}
</body>
</html>
"""


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
    recovered_jobs = db.recover_orphaned_jobs(database_path)
    if recovered_jobs:
        LOGGER.warning("Marked %s orphaned web jobs as interrupted", recovered_jobs)
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
            if parsed.path == "/api/run-status":
                self._send_run_status(database_path, run_id=run_id, context=context)
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
                status_filter=query.get("status", [""])[0],
                csrf_token=context.csrf_token,
                user_id=context.user_id,
                guest_token=context.guest_token,
                context=context,
                source_config=config.sources,
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
                    source_config=config.sources,
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
                    source_config=config.sources,
                )
                self._send_html(body, status=403)
                return
            action = form.get("action", [""])[0]
            run_id: int | None = None
            try:
                identity = (
                    f"user:{context.user_id}"
                    if context.user_id is not None
                    else f"guest:{context.guest_token}"
                )
                _check_rate_limit(database_path, identity, config)
                if action == "login":
                    self._handle_login(form)
                    return
                if action == "register":
                    self._handle_register(form)
                    return
                if action == "logout":
                    self._handle_logout(context)
                    return
                if action in {
                    "save_api_key",
                    "delete_api_key",
                    "test_api_key",
                    "save_supadata_key",
                    "test_supadata_key",
                    "update_supadata_key",
                    "delete_supadata_key",
                }:
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
                    source_config=config.sources,
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

        def _send_run_status(
            self,
            database_path: Path | str,
            *,
            run_id: int | None,
            context: WebContext,
        ) -> None:
            if run_id is None:
                self._send_json({"error": "Run not found."}, status=404)
                return
            payload = run_status_payload(
                database_path,
                run_id=run_id,
                user_id=context.user_id,
                guest_token=context.guest_token,
                csrf_token=context.csrf_token,
                source_config=config.sources,
            )
            if payload is None:
                self._send_json({"error": "Run not found."}, status=404)
                return
            self._send_json(payload)

        def _send_json(self, payload: dict, *, status: int = 200) -> None:
            encoded = json.dumps(payload, separators=(",", ":")).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
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
            supadata_actions = {
                "save_supadata_key",
                "test_supadata_key",
                "update_supadata_key",
                "delete_supadata_key",
            }
            action = form.get("action", [""])[0]
            if action in supadata_actions:
                self._handle_supadata_options_action(form, context, action)
                return
            provider = form.get("provider", [""])[0]
            if action == "delete_api_key":
                db.delete_user_api_key(database_path, user_id=context.user_id, provider=provider)
            elif action == "test_api_key":
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

        def _handle_supadata_options_action(
            self,
            form: dict[str, list[str]],
            context: WebContext,
            action: str,
        ) -> None:
            if context.user_id is None:
                raise ValueError("Login is required.")
            if action == "save_supadata_key":
                save_supadata_api_key(
                    database_path,
                    user_id=context.user_id,
                    label=form.get("label", [""])[0],
                    value=form.get("api_key", [""])[0],
                    priority=_int_form(form, "priority", 100),
                    deployment_secret=config.web.key_encryption_secret,
                )
            else:
                key_id = _int_form(form, "key_id", 0)
                if action == "delete_supadata_key":
                    db.delete_supadata_api_key(
                        database_path,
                        user_id=context.user_id,
                        key_id=key_id,
                    )
                elif action == "update_supadata_key":
                    db.update_supadata_api_key_controls(
                        database_path,
                        user_id=context.user_id,
                        key_id=key_id,
                        label=form.get("label", [""])[0],
                        priority=_int_form(form, "priority", 100),
                        enabled=form.get("enabled", [""])[0] == "1",
                    )
                elif action == "test_supadata_key":
                    row = db.get_supadata_api_key(
                        database_path,
                        user_id=context.user_id,
                        key_id=key_id,
                    )
                    if row is None:
                        raise ValueError("Supadata key not found.")
                    from claimlens.secrets import decrypt_secret

                    key = decrypt_secret(
                        row["encrypted_value"],
                        config.web.key_encryption_secret or "",
                    )
                    try:
                        account = SupadataClient(api_key=key).account_info()
                    except SupadataError as exc:
                        db.mark_supadata_api_key_tested(
                            database_path,
                            user_id=context.user_id,
                            key_id=key_id,
                            status="invalid",
                            last_error=str(exc),
                        )
                    else:
                        status = "ready"
                        if (
                            account.max_credits is not None
                            and account.used_credits is not None
                            and account.used_credits >= account.max_credits
                        ):
                            status = "exhausted"
                        db.mark_supadata_api_key_tested(
                            database_path,
                            user_id=context.user_id,
                            key_id=key_id,
                            status=status,
                            max_credits=account.max_credits,
                            used_credits=account.used_credits,
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


def _render_process_page_legacy(
    database_path: Path | str,
    *,
    run_id: int | None = None,
    notice: str | None = None,
    csrf_token: str = "",
    user_id: int | None = None,
    guest_token: str | None = None,
    context: WebContext | None = None,
    source_config: SourceConfig | None = None,
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

    stepper = ""
    pipeline_badge = ""
    if selected_run is not None:
        step_rows = db.list_run_steps(database_path, selected_run["id"])
        rows = "\n".join(_step_row(row) for row in step_rows)
        stepper = _stepper(step_rows)
        pipeline_badge = _status_badge(selected_run["status"])
        next_step = next_eligible_step(database_path, selected_run["id"])
        if source_config is not None and not source_config.advanced_source_verification:
            next_step = None if next_step == "source_verification" else next_step
        controls = _controls(
            database_path,
            selected_run["id"],
            next_step,
            csrf_token=csrf_token,
            user_id=user_id,
            source_config=source_config,
        )
        outputs = _outputs(database_path, selected_run["video_id"])
        jobs = db.latest_jobs_for_run(database_path, selected_run["id"])
        outputs += _jobs_card(jobs)

    run_options = "\n".join(
        f'<option value="{row["id"]}">#{row["id"]} {html.escape(row["video_id"] or "")}'
        f' - {html.escape(row["status"])}</option>'
        for row in runs
    )
    notice_html = f'<div class="notice">{html.escape(notice)}</div>' if notice else ""

    pipeline_card = ""
    if selected_run is not None:
        video_label = html.escape(selected_run["video_id"] or "")
        pipeline_card = f"""
  <div class="card">
    <div class="card-head">
      <h2>Pipeline &middot; video <span class="mono">{video_label}</span></h2>
      <span id="pipeline-status">{pipeline_badge}</span>
    </div>
    <div id="pipeline-stepper" class="stepper">{stepper}</div>
  </div>
  <div class="card">
    <div class="card-head"><h2>Steps</h2></div>
    <table>
      <thead><tr><th>Step</th><th>Status</th><th>Failure</th><th>Output</th></tr></thead>
      <tbody id="pipeline-steps">{rows}</tbody>
    </table>
    <div class="card-body">
      <div id="pipeline-controls">{controls}</div>
      {_manual_transcript_form(selected_run["id"], csrf_token)}
    </div>
  </div>
"""

    body = f"""
<main>
  <div class="page-head">
    <h1>ClaimLens Process</h1>
    <p>Extract the transcript, analyze the claims, then check them against scientific sources.</p>
  </div>
  {notice_html}
  <div class="card">
    <div class="card-head"><h2>Create Run</h2>
      <span class="sub">One YouTube video per run</span></div>
    <div class="card-body">
      <form method="post" class="row">
        <input type="hidden" name="csrf_token" value="{html.escape(csrf_token)}">
        <input type="hidden" name="action" value="create">
        <label class="field grow" style="flex:1 1 320px">
          <span>Video URL</span>
          <input name="video_url" type="url" required placeholder="https://www.youtube.com/watch?v=...">
        </label>
        <label class="field" style="flex:0 0 160px">
          <span>Report language</span>
          <input name="report_language" value="en">
        </label>
        <button type="submit" class="btn btn-primary">Create</button>
      </form>
    </div>
  </div>
  <div class="card">
    <div class="card-head"><h2>Load Run</h2></div>
    <div class="card-body">
      <form method="get" class="row">
        <label class="field grow"><span>Existing run</span>
          <select name="run_id">{run_options}</select>
        </label>
        <button type="submit" class="btn btn-ghost">Load</button>
      </form>
    </div>
  </div>
  {pipeline_card}
  <div id="pipeline-outputs">{outputs}</div>
</main>
{_live_status_script(selected_run["id"])
 if selected_run is not None and _run_has_active_job(database_path, selected_run["id"])
 else ""}
"""
    return _page_shell(
        "ClaimLens Process",
        body,
        context=context,
        csrf_token=csrf_token,
        active="process",
    )


def render_process_page(
    database_path: Path | str,
    *,
    run_id: int | None = None,
    notice: str | None = None,
    csrf_token: str = "",
    user_id: int | None = None,
    guest_token: str | None = None,
    context: WebContext | None = None,
    source_config: SourceConfig | None = None,
    status_filter: str = "",
) -> str:
    runs = (
        db.list_visible_pipeline_runs(database_path, user_id=user_id, guest_token=guest_token)
        if user_id is not None or guest_token
        else db.list_pipeline_runs(database_path)
    )
    allowed_filters = {"running", "succeeded", "failed", "completed_with_warnings"}
    if status_filter in allowed_filters:
        runs = [row for row in runs if row["status"] == status_filter]
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
    notice_html = f'<div class="notice">{html.escape(notice)}</div>' if notice else ""
    create_card = f"""
  <div class="card">
    <div class="card-head"><h2>New analysis</h2>
      <span class="sub">One YouTube video per analysis</span></div>
    <div class="card-body">
      <form method="post" class="row">
        <input type="hidden" name="csrf_token" value="{html.escape(csrf_token)}">
        <input type="hidden" name="action" value="create">
        <label class="field grow" style="flex:1 1 320px">
          <span>YouTube video URL</span>
          <input name="video_url" type="url" required placeholder="https://www.youtube.com/watch?v=...">
        </label>
        <label class="field" style="flex:0 0 160px">
          <span>Report language</span>
          <input name="report_language" value="en">
        </label>
        <button type="submit" class="btn btn-primary">Start analysis</button>
      </form>
    </div>
  </div>
"""
    active_workspace = ""
    if selected_run is not None:
        step_rows = db.list_run_steps(database_path, selected_run["id"])
        next_step = next_eligible_step(database_path, selected_run["id"])
        if source_config is not None and not source_config.advanced_source_verification:
            next_step = None if next_step == "source_verification" else next_step
        active_workspace = _active_workspace(
            database_path,
            selected_run,
            step_rows,
            next_step,
            csrf_token=csrf_token,
            user_id=user_id,
            source_config=source_config,
        )
    body = f"""
<main>
  <div class="page-head">
    <h1>Analyses</h1>
    <p>Track transcript extraction, claim analysis, and evidence review in one workspace.</p>
  </div>
  {notice_html}
  {create_card}
  {active_workspace}
  {_history_card(runs, selected_run["id"] if selected_run is not None else None, status_filter)}
</main>
{_live_status_script(selected_run["id"])
 if selected_run is not None and _run_has_active_job(database_path, selected_run["id"])
 else ""}
"""
    return _page_shell(
        "ClaimLens Analyses",
        body,
        context=context,
        csrf_token=csrf_token,
        active="process",
    )


def _active_workspace(
    database_path: Path | str,
    selected_run,
    step_rows,
    next_step: str | None,
    *,
    csrf_token: str,
    user_id: int | None,
    source_config: SourceConfig | None,
) -> str:
    step_by_name = {row["step"]: row for row in step_rows}
    captions_row = step_by_name.get("captions")
    failed_captions = captions_row is not None and captions_row["status"] == "failed"
    controls = _controls(
        database_path,
        selected_run["id"],
        next_step,
        csrf_token=csrf_token,
        user_id=user_id,
        source_config=source_config,
    )
    recovery = _manual_transcript_form(selected_run["id"], csrf_token) if failed_captions else ""
    active_label, active_message = _active_action(selected_run, next_step, failed_captions)
    video_id = html.escape(selected_run["video_id"] or "")
    video_url = html.escape(selected_run["source_url"] or selected_run["video_id"] or "")
    step_rows_html = "\n".join(_step_row(row) for row in step_rows)
    jobs = db.latest_jobs_for_run(database_path, selected_run["id"])
    jobs_html = ""
    if jobs:
        jobs_html = f"""
        <h3>Background actions</h3>
        <div class="table-wrap"><table>
          <thead><tr><th>Action</th><th>Status</th><th>Message</th></tr></thead>
          <tbody>{''.join(_job_row(row) for row in jobs)}</tbody>
        </table></div>
        """
    diagnostics = f"""
    <details class="diagnostic">
      <summary>Execution details</summary>
      <div class="diagnostic-body">
        <div id="pipeline-stepper" class="stepper">{_stepper(step_rows)}</div>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Step</th><th>Status</th><th>Details</th><th>Output</th></tr></thead>
            <tbody id="pipeline-steps">{step_rows_html}</tbody>
          </table>
        </div>
        {jobs_html}
      </div>
    </details>
"""
    return f"""
  <section class="workspace" aria-label="Active analysis workspace">
    <div class="workspace-main">
      <div class="card">
        <div class="card-head">
          <div>
            <div class="workspace-title"><h2>Active analysis</h2>
              <span id="pipeline-status">{_status_badge(selected_run["status"])}</span></div>
            <p class="workspace-url">Video <span class="mono">{video_id}</span> · {video_url}</p>
          </div>
        </div>
        <div class="card-body">
          <div class="workspace-action">
            <h3>{html.escape(active_label)}</h3>
            <p>{html.escape(active_message)}</p>
            <div id="pipeline-controls">{controls}</div>
            {recovery}
          </div>
          {diagnostics}
        </div>
      </div>
      <div id="pipeline-outputs">{_outputs(database_path, selected_run["video_id"])}</div>
    </div>
  </section>
"""


def _active_action(selected_run, next_step: str | None, failed_captions: bool) -> tuple[str, str]:
    if failed_captions:
        return (
            "Transcript recovery needed",
            "Captions could not be retrieved. Paste a transcript to continue.",
        )
    if next_step:
        label = _step_label(next_step)
        return f"Next: {label}", f"Continue with {label.lower()} when you are ready."
    if selected_run["status"] == "running":
        return (
            "Analysis in progress",
            "ClaimLens is processing this analysis. This view updates automatically.",
        )
    if selected_run["status"] == "completed_with_warnings":
        return (
            "Review verification limits",
            "The analysis completed, but one or more evidence providers returned warnings.",
        )
    if selected_run["status"] == "succeeded":
        return "Analysis complete", "The brief and available evidence summary are ready to review."
    return (
        _status_label(selected_run["status"]),
        "Review the execution details for the next available recovery action.",
    )


def _history_card(runs, selected_run_id: int | None, status_filter: str) -> str:
    options = "".join(
        f'<option value="{value}"{" selected" if value == status_filter else ""}>{label}</option>'
        for value, label in [
            ("", "All statuses"),
            ("running", "In progress"),
            ("succeeded", "Complete"),
            ("completed_with_warnings", "With limits"),
            ("failed", "Needs attention"),
        ]
    )
    rows = "".join(
        f'<div class="history-row"><div><a href="/?run_id={row["id"]}">'
        f'{html.escape(row["video_id"] or "Untitled analysis")}</a>'
        f'<small>Analysis #{row["id"]} · {html.escape(row["started_at"] or "")}</small></div>'
        f'{_status_badge(row["status"])}</div>'
        for row in runs
    )
    empty = '<p class="mono">No analyses match this status.</p>' if not rows else rows
    return f"""
  <div class="card">
    <div class="card-head"><h2>Recent analyses</h2>
      <form method="get"><label class="sr-only" for="status-filter">Filter analyses</label>
        <select id="status-filter" class="history-filter" name="status"
          onchange="this.form.submit()">{options}</select></form>
    </div>
    <div class="card-body"><div class="history-list">{empty}</div></div>
  </div>
"""


def _stepper(step_rows) -> str:
    cells = []
    for index, row in enumerate(step_rows, start=1):
        status = (row["status"] or "").lower()
        if status == "succeeded":
            cls, glyph = "done", "&check;"
        elif status == "completed_with_warnings":
            cls, glyph = "active", "!"
        elif status == "running":
            cls, glyph = "active", str(index)
        elif status == "failed":
            cls, glyph = "bad", "&times;"
        else:
            cls, glyph = "", str(index)
        name = html.escape(_step_label(row["step"]))
        meta = html.escape(_status_label(row["status"] or "pending"))
        cells.append(
            f'<div class="step {cls}"><div class="dot">{glyph}</div>'
            f'<div class="name">{name}</div><div class="meta">{meta}</div></div>'
        )
    return "".join(cells)


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
    completed_run = db.get_pipeline_run(database_path, run_id)
    completed_with_warnings = (
        completed_run is not None and completed_run["status"] == "completed_with_warnings"
    )
    db.update_job(
        database_path,
        job_id=job_id,
        status="completed_with_warnings" if completed_with_warnings else "succeeded",
        progress=100,
        message="Completed with warnings" if completed_with_warnings else "Completed",
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
        extract_required_subtitles(database_path, run_id, config=config, user_id=user_id)
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
        if not config.sources.advanced_source_verification:
            raise ValueError("Advanced source verification is disabled in configuration.")
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
        adapters = default_adapters(
            semantic_scholar_key=semantic_key,
            ncbi_key=ncbi_key,
            enable_pubmed=config.sources.enable_pubmed,
            enable_semantic_scholar=config.sources.enable_semantic_scholar,
        )
        if not adapters:
            raise ValueError("No source-verification adapters are enabled in configuration.")
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
        verification = db.latest_verification_run(database_path, run["video_id"])
        verification_status = verification["status"] if verification is not None else "failed"
        db.set_step_status(
            database_path,
            run_id=run_id,
            step="source_verification",
            status=verification_status,
            output_path=str(path),
            failure_message=(
                verification["failure_message"]
                if verification_status == "completed_with_warnings" and verification is not None
                else None
            ),
        )
        db.set_run_status(
            database_path,
            run_id=run_id,
            status=verification_status,
            current_step="source_verification",
            failure_message=(
                verification["failure_message"]
                if verification_status == "completed_with_warnings" and verification is not None
                else None
            ),
        )
        _ = verification_run_id
        return path
    else:
        raise ValueError(f"Unsupported action: {action}")


def _controls(
    database_path: Path | str,
    run_id: int,
    next_step: str | None,
    *,
    csrf_token: str = "",
    user_id: int | None = None,
    source_config: SourceConfig | None = None,
) -> str:
    if next_step is None:
        return ""
    secret = ""
    saved_providers = (
        {row["provider"] for row in db.list_user_api_keys(database_path, user_id=user_id)}
        if user_id is not None
        else set()
    )
    if next_step == "analysis":
        if "openai" not in saved_providers:
            secret = (
                '<label class="field grow"><span>OpenAI API key</span>'
                '<input name="openai_api_key" type="password" placeholder="OpenAI API key">'
                "</label>"
            )
    elif next_step == "source_verification":
        fields = []
        if (
            (source_config is None or source_config.enable_semantic_scholar)
            and "semantic_scholar" not in saved_providers
        ):
            fields.append(
                '<label class="field grow"><span>Semantic Scholar API key</span>'
                '<input name="semantic_scholar_api_key" type="password" '
                'placeholder="Semantic Scholar API key"></label>'
            )
        if (source_config is None or source_config.enable_pubmed) and "ncbi" not in saved_providers:
            fields.append(
                '<label class="field grow"><span>NCBI API key</span>'
                '<input name="ncbi_api_key" type="password" placeholder="NCBI API key"></label>'
            )
        secret = "".join(fields)
    return f"""
    <form method="post" class="row" style="margin-top:16px">
      <input type="hidden" name="csrf_token" value="{html.escape(csrf_token)}">
      <input type="hidden" name="run_id" value="{run_id}">
      <input type="hidden" name="action" value="{html.escape(next_step)}">
      {secret}
      <button type="submit" class="btn btn-primary">Run {
          html.escape(next_step.replace("_", " "))}</button>
    </form>
    """


def _jobs_card(jobs) -> str:
    job_rows = "".join(_job_row(row) for row in jobs)
    if not job_rows:
        return ""
    return (
        '<div class="card"><div class="card-head"><h2>Jobs</h2></div><table>'
        "<thead><tr><th>Action</th><th>Status</th><th>Message</th></tr></thead>"
        f"<tbody id=\"pipeline-jobs\">{job_rows}</tbody></table></div>"
    )


def _run_has_active_job(database_path: Path | str, run_id: int) -> bool:
    return any(
        row["status"] in {"queued", "running"}
        for row in db.latest_jobs_for_run(database_path, run_id)
    )


def run_status_payload(
    database_path: Path | str,
    *,
    run_id: int,
    user_id: int | None,
    guest_token: str | None,
    csrf_token: str = "",
    source_config: SourceConfig | None = None,
) -> dict | None:
    """Return the safe, renderable state needed by the live Process page."""

    run = db.get_visible_pipeline_run(
        database_path,
        run_id,
        user_id=user_id,
        guest_token=guest_token,
    )
    if run is None:
        return None
    step_rows = db.list_run_steps(database_path, run_id)
    jobs = db.latest_jobs_for_run(database_path, run_id)
    next_step = next_eligible_step(database_path, run_id)
    if source_config is not None and not source_config.advanced_source_verification:
        next_step = None if next_step == "source_verification" else next_step
    outputs = _outputs(database_path, run["video_id"]) + _jobs_card(jobs)
    state = {
        "run": {
            "status": run["status"],
            "current_step": run["current_step"],
            "failure_message": run["failure_message"],
        },
        "steps": [
            {
                "step": row["step"],
                "status": row["status"],
                "failure_message": row["failure_message"],
                "output_path": row["output_path"],
                "updated_at": row["updated_at"],
            }
            for row in step_rows
        ],
        "jobs": [
            {
                "id": row["id"],
                "action": row["action"],
                "status": row["status"],
                "message": row["message"],
                "output_path": row["output_path"],
                "updated_at": row["updated_at"],
            }
            for row in jobs
        ],
        "next_step": next_step,
    }
    return {
        "signature": json.dumps(state, sort_keys=True, separators=(",", ":")),
        "active": any(row["status"] in {"queued", "running"} for row in jobs),
        "pipeline_status_html": _status_badge(run["status"]),
        "stepper_html": _stepper(step_rows),
        "steps_html": "\n".join(_step_row(row) for row in step_rows),
        "controls_html": _controls(
            database_path,
            run_id,
            next_step,
            csrf_token=csrf_token,
            user_id=user_id,
            source_config=source_config,
        ),
        "outputs_html": outputs,
    }


def _live_status_script(run_id: int) -> str:
    return f"""
<script>
(() => {{
  const endpoint = "/api/run-status?run_id={run_id}";
  const regions = {{
    pipeline: document.getElementById("pipeline-status"),
    stepper: document.getElementById("pipeline-stepper"),
    steps: document.getElementById("pipeline-steps"),
    controls: document.getElementById("pipeline-controls"),
    outputs: document.getElementById("pipeline-outputs")
  }};
  let signature = null;
  let inFlight = false;

  const schedule = (delay) => window.setTimeout(refresh, delay);
  async function refresh() {{
    if (inFlight) return;
    inFlight = true;
    try {{
      const response = await fetch(endpoint, {{cache: "no-store", credentials: "same-origin"}});
      if (!response.ok) {{ schedule(5000); return; }}
      const state = await response.json();
      if (state.signature !== signature) {{
        regions.pipeline.innerHTML = state.pipeline_status_html;
        regions.stepper.innerHTML = state.stepper_html;
        regions.steps.innerHTML = state.steps_html;
        regions.controls.innerHTML = state.controls_html;
        regions.outputs.innerHTML = state.outputs_html;
        signature = state.signature;
      }}
      if (state.active) schedule(2000);
    }} catch (_error) {{
      schedule(5000);
    }} finally {{
      inFlight = false;
    }}
  }}
  refresh();
}})();
</script>
"""


def _manual_transcript_form(run_id: int, csrf_token: str) -> str:
    return f"""
    <div class="recovery-panel">
      <h4>Paste a transcript fallback</h4>
      <p>Use this recovery path when captions are unavailable for the video.</p>
    <form method="post" style="margin-top:14px;display:grid;gap:12px">
      <input type="hidden" name="csrf_token" value="{html.escape(csrf_token)}">
      <input type="hidden" name="run_id" value="{run_id}">
      <input type="hidden" name="action" value="manual_transcript">
      <label class="field" style="max-width:220px"><span>Transcript language</span>
        <input name="transcript_language" value="unknown">
      </label>
      <label class="field"><span>Paste transcript fallback</span>
        <textarea name="transcript_text"
          placeholder="Paste .txt, .srt, or .vtt text here"></textarea>
      </label>
      <div><button type="submit" class="btn btn-ghost">Use pasted transcript</button></div>
    </form>
    </div>
    """


def _outputs(database_path: Path | str, video_id: str) -> str:
    cleaned = db.get_cleaned_transcript(database_path, video_id)
    brief = db.latest_brief_artifact(database_path, video_id)
    verification = db.latest_verification_run(database_path, video_id)
    video = db.get_video(database_path, video_id)
    analysis = db.latest_analysis(database_path, video_id)
    claims = db.claims_for_summary(database_path, analysis["id"]) if analysis else []
    evidence = (
        db.evidence_for_verification(database_path, verification["id"])
        if verification
        else []
    )
    brief_status = brief["source_verification_status"] if brief else "not_available"
    if brief_status == "advanced_source_verified":
        report_label = "Evidence-backed brief"
    elif brief_status == "advanced_source_verified_with_warnings":
        report_label = "Verification attempt with limits"
    elif brief:
        report_label = "Analysis brief"
    else:
        report_label = "Not available"
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
    result_status = (
        "completed_with_warnings"
        if verification and verification["status"] == "completed_with_warnings"
        else "succeeded"
        if brief
        else "pending"
    )
    return (
        '<div class="card"><div class="card-head"><h2>Results</h2>'
        f'{_status_badge(result_status)}</div><div class="card-body">'
        f'<div class="summary-grid">'
        f'<div class="summary-item"><strong>{len(claims)}</strong>'
        f'<span>Claims reviewed</span></div>'
        f'<div class="summary-item"><strong>{len(evidence)}</strong>'
        f'<span>Evidence snippets</span></div>'
        f'<div class="summary-item"><strong>{html.escape(report_label)}</strong>'
        f'<span>Report status</span></div></div>'
        f'<ul class="out">{"".join(links)}</ul>{preview}</div></div>'
    )


def _nav(context: WebContext | None, csrf_token: str, *, active: str | None = None) -> str:
    logged_in = context is not None and context.user_id is not None
    analyses_cls = ' class="active"' if active == "process" else ""
    links = f'<a href="/"{analyses_cls}>Analyses</a>'
    if logged_in:
        options_cls = ' class="active"' if active == "options" else ""
        links += f'<a href="/options"{options_cls}>Options</a>'
        initial = html.escape((context.email or "?")[:1].upper())
        user = (
            f'<span class="who">{html.escape(context.email or "")}</span>'
            '<form method="post" style="display:inline">'
            f'<input type="hidden" name="csrf_token" value="{html.escape(csrf_token)}">'
            '<input type="hidden" name="action" value="logout">'
            '<button type="submit" class="btn btn-ghost btn-sm">Logout</button></form>'
            f'<span class="avatar">{initial}</span>'
        )
    else:
        user = '<a href="/login" class="btn btn-ghost btn-sm">Login</a>'
    return (
        '<nav class="app">'
        f'<a class="brand" href="/"><span class="mark">{LOGO_MARK}</span> ClaimLens</a>'
        f'<div class="navlinks">{links}</div>'
        f'<div class="navuser">{user}</div>'
        "</nav>"
    )


def render_login_page(*, context: WebContext, notice: str | None = None) -> str:
    notice_html = f'<div class="notice">{html.escape(notice)}</div>' if notice else ""
    csrf = html.escape(context.csrf_token)
    body = f"""
<div class="auth-wrap">
  <div class="card auth-card">
    <div class="card-body">
      <div class="auth-logo">
        <span class="mark">{LOGO_MARK}</span>
        <div><h1>Login</h1>
          <p class="mono" style="color:var(--muted)">Sign in to your ClaimLens analyses</p></div>
      </div>
      {notice_html}
      <form method="post" style="display:grid;gap:14px">
        <input type="hidden" name="csrf_token" value="{csrf}">
        <input type="hidden" name="action" value="login">
        <label class="field"><span>Email</span>
          <input name="email" type="email" required></label>
        <label class="field"><span>Password</span>
          <input name="password" type="password" required></label>
        <button type="submit" class="btn btn-primary" style="width:100%">Login</button>
      </form>
      <div class="divider">Create first account</div>
      <form method="post" style="display:grid;gap:14px">
        <input type="hidden" name="csrf_token" value="{csrf}">
        <input type="hidden" name="action" value="register">
        <label class="field"><span>Email</span>
          <input name="email" type="email" required></label>
        <label class="field"><span>Password</span>
          <input name="password" type="password" required></label>
        <button type="submit" class="btn btn-ghost" style="width:100%">Create account</button>
      </form>
    </div>
  </div>
</div>
"""
    return _page_shell(
        "ClaimLens Login",
        body,
        context=context,
        csrf_token=context.csrf_token,
        active=None,
    )


def render_options_page(
    database_path: Path | str,
    config: AppConfig,
    *,
    context: WebContext,
) -> str:
    if context.user_id is None:
        return _page_shell(
            "ClaimLens Options",
            '<main><div class="notice">Login is required.</div></main>',
            context=context,
            csrf_token=context.csrf_token,
        )
    rows = db.list_user_api_keys(database_path, user_id=context.user_id)
    status = {row["provider"]: row for row in rows}
    sections = []
    for provider, label in [
        ("openai", "OpenAI"),
        ("semantic_scholar", "Semantic Scholar"),
        ("ncbi", "NCBI / PubMed"),
    ]:
        row = status.get(provider)
        if row:
            saved = (
                f"Saved: <span class=\"mono\">{html.escape(row['masked_value'])}</span>, "
                f"updated {html.escape(row['updated_at'])}"
                + (
                    f", tested {html.escape(row['tested_at'])}"
                    if row["tested_at"]
                    else ""
                )
            )
            badge = _status_badge("succeeded" if row["tested_at"] else "saved")
        else:
            saved = "No saved key."
            badge = _status_badge("idle")
        csrf = html.escape(context.csrf_token)
        sections.append(
            f"""
            <div class="card">
              <div class="card-head"><h2>{label}</h2>{badge}</div>
              <div class="card-body">
                <p style="margin:0 0 16px;color:var(--muted);font-size:13.5px">{saved}</p>
                <form method="post" class="row">
                  <input type="hidden" name="csrf_token" value="{csrf}">
                  <input type="hidden" name="action" value="save_api_key">
                  <input type="hidden" name="provider" value="{provider}">
                  <label class="field grow"><span>API key</span>
                    <input name="api_key" type="password" required></label>
                  <button type="submit" class="btn btn-primary">Save key</button>
                </form>
                <div class="row" style="margin-top:12px">
                  <form method="post" style="display:inline">
                    <input type="hidden" name="csrf_token" value="{csrf}">
                    <input type="hidden" name="action" value="test_api_key">
                    <input type="hidden" name="provider" value="{provider}">
                    <button type="submit" class="btn btn-ghost btn-sm">Test saved key</button>
                  </form>
                  <form method="post" style="display:inline">
                    <input type="hidden" name="csrf_token" value="{csrf}">
                    <input type="hidden" name="action" value="delete_api_key">
                    <input type="hidden" name="provider" value="{provider}">
                    <button type="submit" class="btn btn-danger btn-sm">Delete key</button>
                  </form>
                </div>
              </div>
            </div>
            """
        )
    secret_notice = (
        ""
        if config.web.key_encryption_secret
        else '<div class="notice">Set CLAIMLENS_KEY_ENCRYPTION_SECRET before saving keys.</div>'
    )
    body = f"""
<main>
  <div class="page-head">
    <h1>Options</h1>
    <p>Your API keys are encrypted at rest and only power your own analyses.</p>
  </div>
  {secret_notice}
  {''.join(sections)}
  {_supadata_options_section(database_path, context)}
</main>
"""
    return _page_shell(
        "ClaimLens Options",
        body,
        context=context,
        csrf_token=context.csrf_token,
        active="options",
    )


def _supadata_options_section(database_path: Path | str, context: WebContext) -> str:
    if context.user_id is None:
        return ""
    csrf = html.escape(context.csrf_token)
    rows = db.list_supadata_api_keys(database_path, user_id=context.user_id)
    key_rows = []
    for row in rows:
        quota = "quota unknown"
        if row["max_credits"] is not None and row["used_credits"] is not None:
            quota = f"{row['used_credits']} / {row['max_credits']} credits"
        enabled = "checked" if row["enabled"] else ""
        status = html.escape(row["status"])
        key_rows.append(
            f"""
            <div class="card" style="box-shadow:none;border-color:var(--line-2)">
              <div class="card-head">
                <h3>{html.escape(row['label'])}</h3>
                {_status_badge(status)}
              </div>
              <div class="card-body">
                <p style="margin:0 0 12px;color:var(--muted);font-size:13.5px">
                  <span class="mono">{html.escape(row['masked_value'])}</span> · {quota}
                  · monthly native requests: {row['monthly_request_count']}
                </p>
                <form method="post" class="row">
                  <input type="hidden" name="csrf_token" value="{csrf}">
                  <input type="hidden" name="action" value="update_supadata_key">
                  <input type="hidden" name="key_id" value="{row['id']}">
                  <label class="field grow"><span>Label</span>
                    <input name="label" value="{html.escape(row['label'])}"></label>
                  <label class="field"><span>Priority</span>
                    <input name="priority" type="number" value="{row['priority']}"></label>
                  <label class="check"><input name="enabled" value="1" type="checkbox" {enabled}>
                    Enabled</label>
                  <button type="submit" class="btn btn-ghost btn-sm">Update</button>
                </form>
                <div class="row" style="margin-top:12px">
                  <form method="post" style="display:inline">
                    <input type="hidden" name="csrf_token" value="{csrf}">
                    <input type="hidden" name="action" value="test_supadata_key">
                    <input type="hidden" name="key_id" value="{row['id']}">
                    <button type="submit" class="btn btn-ghost btn-sm">Test quota</button>
                  </form>
                  <form method="post" style="display:inline">
                    <input type="hidden" name="csrf_token" value="{csrf}">
                    <input type="hidden" name="action" value="delete_supadata_key">
                    <input type="hidden" name="key_id" value="{row['id']}">
                    <button type="submit" class="btn btn-danger btn-sm">Delete key</button>
                  </form>
                </div>
              </div>
            </div>
            """
        )
    saved = "".join(key_rows) or "<p>No Supadata keys saved.</p>"
    return f"""
  <div class="card">
    <div class="card-head"><h2>Supadata native captions</h2>{_status_badge('native')}</div>
    <div class="card-body">
      <p style="margin:0 0 16px;color:var(--muted);font-size:13.5px">
        ClaimLens only requests Supadata transcripts with <span class="mono">mode=native</span>
        and <span class="mono">text=false</span>. Auto and generated transcript modes are not used.
      </p>
      <form method="post" class="row">
        <input type="hidden" name="csrf_token" value="{csrf}">
        <input type="hidden" name="action" value="save_supadata_key">
        <label class="field grow"><span>Label</span><input name="label" required></label>
        <label class="field"><span>Priority</span>
          <input name="priority" type="number" value="100"></label>
        <label class="field grow"><span>Supadata API key</span>
          <input name="api_key" type="password" required></label>
        <button type="submit" class="btn btn-primary">Add key</button>
      </form>
      <div style="margin-top:16px">{saved}</div>
    </div>
  </div>
"""


def _verification_counts(database_path: Path | str, verification_run_id: int) -> str:
    evidence = db.evidence_for_verification(database_path, verification_run_id)
    supports = sum(1 for row in evidence if row["polarity"] == "supports")
    contradicts = sum(1 for row in evidence if row["polarity"] == "contradicts")
    return f"{supports} supporting snippets, {contradicts} contradicting snippets"


def _step_row(row) -> str:
    return (
        "<tr>"
        f"<td class=\"name\">{html.escape(_step_label(row['step']))}</td>"
        f"<td class=\"status\">{_status_badge(row['status'])}</td>"
        f"<td>{html.escape(row['failure_message'] or '')}</td>"
        f"<td class=\"mono\">{html.escape(row['output_path'] or '')}</td>"
        "</tr>"
    )


def _job_row(row) -> str:
    return (
        "<tr>"
        f"<td class=\"name\">{html.escape(_step_label(row['action']))}</td>"
        f"<td class=\"status\">{_status_badge(row['status'])}</td>"
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
    download = ""
    if path is None:
        content = '<div class="notice">No report is available for this run.</div>'
    else:
        content = _markdown_to_html(path.read_text(encoding="utf-8"))
        if run_id is not None:
            download = (
                f'<a href="/brief/download?run_id={run_id}" '
                'class="btn btn-ghost btn-sm">Download .md</a>'
            )
    body = f"""
<main>
  <div class="card report">
    <div class="card-head"><h2>Verification brief</h2>{download}</div>
    <div class="card-body">{content}</div>
  </div>
</main>
"""
    return _page_shell(
        "ClaimLens Report",
        body,
        context=context,
        csrf_token=context.csrf_token if context else "",
        active="process",
        nav=context is not None,
    )


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


def _check_rate_limit(database_path: Path | str, identity: str, config: AppConfig) -> None:
    if not db.record_rate_limit_event(
        database_path,
        identity=identity,
        window_seconds=config.web.rate_limit_window_seconds,
        max_actions=config.web.rate_limit_actions,
    ):
        raise ValueError("Too many actions submitted recently. Wait and try again.")


def _public_error(exc: Exception) -> str:
    text = str(exc).strip()
    if not text:
        return "The action failed."
    if "/" in text or "\\" in text:
        return "The action failed. Check the application logs for details."
    return text
