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
.step:not(:last-child)::after { content:""; position:absolute; top:30px; right:-1px; width:1px;
  height:calc(100% - 24px); background:var(--line-2); }
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
@media (max-width:720px) {
  .stepper { grid-template-columns:1fr 1fr; }
  .report .card-body { padding:24px; }
  .navuser .who { display:none; }
}
@media (prefers-reduced-motion: reduce) { * { transition:none !important; } }
"""


def _badge_class(status: str) -> str:
    return {
        "succeeded": "ok",
        "completed": "ok",
        "running": "run",
        "failed": "bad",
    }.get((status or "").lower(), "idle")


def _status_badge(status: str, *, suffix: str = "") -> str:
    label = html.escape((status or "").replace("_", " ")) + suffix
    return f'<span class="badge {_badge_class(status)}">{label}</span>'


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

    stepper = ""
    pipeline_badge = ""
    if selected_run is not None:
        step_rows = db.list_run_steps(database_path, selected_run["id"])
        rows = "\n".join(_step_row(row) for row in step_rows)
        stepper = _stepper(step_rows)
        pipeline_badge = _status_badge(selected_run["status"])
        next_step = next_eligible_step(database_path, selected_run["id"])
        controls = _controls(selected_run["id"], next_step, csrf_token=csrf_token)
        outputs = _outputs(database_path, selected_run["video_id"])
        jobs = db.latest_jobs_for_run(database_path, selected_run["id"])
        job_rows = "".join(_job_row(row) for row in jobs)
        if job_rows:
            outputs += (
                '<div class="card"><div class="card-head"><h2>Jobs</h2></div><table>'
                "<thead><tr><th>Action</th><th>Status</th><th>Progress</th><th>Message</th></tr></thead>"
                f"<tbody>{job_rows}</tbody></table></div>"
            )

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
      {pipeline_badge}
    </div>
    <div class="stepper">{stepper}</div>
  </div>
  <div class="card">
    <div class="card-head"><h2>Steps</h2></div>
    <table>
      <thead><tr><th>Step</th><th>Status</th><th>Failure</th><th>Output</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>
    <div class="card-body">
      {controls}
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
  {outputs}
</main>
"""
    return _page_shell(
        "ClaimLens Process",
        body,
        context=context,
        csrf_token=csrf_token,
        active="process",
    )


def _stepper(step_rows) -> str:
    cells = []
    for index, row in enumerate(step_rows, start=1):
        status = (row["status"] or "").lower()
        if status == "succeeded":
            cls, glyph = "done", "&check;"
        elif status == "running":
            cls, glyph = "active", str(index)
        elif status == "failed":
            cls, glyph = "bad", "&times;"
        else:
            cls, glyph = "", str(index)
        name = html.escape(row["step"].replace("_", " "))
        meta = html.escape(row["status"] or "pending")
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
            '<label class="field grow"><span>OpenAI API key</span>'
            '<input name="openai_api_key" type="password" placeholder="OpenAI API key">'
            "</label>"
        )
    elif next_step == "source_verification":
        secret = (
            '<label class="field grow"><span>Semantic Scholar API key</span>'
            '<input name="semantic_scholar_api_key" type="password" '
            'placeholder="Semantic Scholar API key"></label>'
            '<label class="field grow"><span>NCBI API key</span>'
            '<input name="ncbi_api_key" type="password" placeholder="NCBI API key"></label>'
        )
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


def _manual_transcript_form(run_id: int, csrf_token: str) -> str:
    return f"""
    <form method="post" style="margin-top:20px;display:grid;gap:12px">
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
    return (
        '<div class="card"><div class="card-head"><h2>Outputs</h2></div>'
        f'<div class="card-body"><ul class="out">{"".join(links)}</ul>{preview}</div></div>'
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
</main>
"""
    return _page_shell(
        "ClaimLens Options",
        body,
        context=context,
        csrf_token=context.csrf_token,
        active="options",
    )


def _verification_counts(database_path: Path | str, verification_run_id: int) -> str:
    evidence = db.evidence_for_verification(database_path, verification_run_id)
    supports = sum(1 for row in evidence if row["polarity"] == "supports")
    contradicts = sum(1 for row in evidence if row["polarity"] == "contradicts")
    return f"{supports} supporting snippets, {contradicts} contradicting snippets"


def _step_row(row) -> str:
    return (
        "<tr>"
        f"<td class=\"name\">{html.escape(row['step'].replace('_', ' '))}</td>"
        f"<td class=\"status\">{_status_badge(row['status'])}</td>"
        f"<td>{html.escape(row['failure_message'] or '')}</td>"
        f"<td class=\"mono\">{html.escape(row['output_path'] or '')}</td>"
        "</tr>"
    )


def _job_row(row) -> str:
    return (
        "<tr>"
        f"<td class=\"name\">{html.escape(row['action'].replace('_', ' '))}</td>"
        f"<td class=\"status\">{_status_badge(row['status'])}</td>"
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
