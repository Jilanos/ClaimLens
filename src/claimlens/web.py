"""Local HTML process page for one-video runs."""

from __future__ import annotations

import html
import json
import logging
import os
import re
import secrets
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, urlparse

from claimlens import __version__, db
from claimlens.analysis import OpenAIAnalysisClient, analyze_cleaned_transcript
from claimlens.api_keys import (
    ApiKeyTestError,
    KeyContext,
    keyring_for_config,
    resolve_api_key,
    save_supadata_api_key,
    save_user_api_key,
    validate_provider_api_key,
)
from claimlens.assets import LIVE_STATUS_JS
from claimlens.auth import (
    guest_csrf_token,
    hash_password,
    new_guest_token,
    new_session_token,
    token_digest,
    verify_password,
)
from claimlens.briefs import SIGNALS_PREFIX, generate_brief, generate_verified_brief
from claimlens.config import AppConfig, SourceConfig
from claimlens.evidence import (
    OpenAIClaimSynthesizer,
    OpenAIClaimTranslator,
    OpenAIEvidenceGrader,
)
from claimlens.kapsule_auth import authenticate as authenticate_kapsule_account
from claimlens.pipeline import (
    add_manual_transcript,
    clean_run_transcript,
    create_run,
    extract_required_subtitles,
    next_chained_step,
    next_eligible_step,
)
from claimlens.verification import default_adapters, verify_sources
from claimlens.youtube import SupadataClient, SupadataError

LOGGER = logging.getLogger(__name__)
DEFAULT_JOB_WORKERS = 4


def _job_workers() -> int:
    """Size the worker pool, which now bounds concurrent runs rather than steps.

    A worker stays busy for a whole chain, so this is the number of analyses that can
    progress at once.
    """

    try:
        value = int(os.environ.get("CLAIMLENS_JOB_WORKERS", DEFAULT_JOB_WORKERS))
    except ValueError:
        return DEFAULT_JOB_WORKERS
    return max(1, min(value, 16))


EXECUTOR = ThreadPoolExecutor(max_workers=_job_workers(), thread_name_prefix="claimlens-job")
STEP_LABELS = {
    "captions": "Get captions",
    "clean_transcript": "Prepare transcript",
    "analysis": "Analyze claims",
    "brief": "Create brief",
    "source_verification": "Check sources",
}
#: Analyses shown before the history collapses into a disclosure.
HISTORY_VISIBLE_ROWS = 8
#: A brief line no longer than this and ending in a colon reads as a sub-heading.
BRIEF_SUBHEAD_MAX_CHARS = 60
MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
#: Run statuses that may still be overtaken by the work they describe.
UNSETTLED_RUN_STATUSES = frozenset({"created", "running", "pending"})
#: Regions a poll may repaint, mapped to the payload key that carries their HTML. The page
#: hands this map to the browser client, so the server alone decides what is live.
LIVE_REGIONS = {
    "pipeline-status": "pipeline_status_html",
    "pipeline-stepper": "stepper_html",
    "pipeline-steps": "steps_html",
    "pipeline-action": "action_html",
    "pipeline-controls": "controls_html",
    "pipeline-recovery": "recovery_html",
    "pipeline-outputs": "outputs_html",
    "pipeline-brief": "brief_html",
}
LIVE_CONNECTION_REGION = "pipeline-connection"
LIVE_OFFLINE_MESSAGE = "Live updates are unavailable. Retrying automatically."
LIVE_ACTIVE_DELAY_MS = 2000
LIVE_IDLE_DELAY_MS = 15000
LIVE_ERROR_DELAY_MS = 5000
#: One failed poll is noise; a second in a row is worth telling the reader about.
LIVE_ERRORS_BEFORE_NOTICE = 2
LIVE_STATUS_ASSET = "/static/live-status.js"
#: Job states that still have work in flight.
LIVE_JOB_STATUSES = frozenset({"queued", "running"})
STATUS_LABELS = {
    "queued": "Queued",
    "running": "In progress",
    "succeeded": "Complete",
    "completed_with_warnings": "Complete with limits",
    "failed": "Needs attention",
    "interrupted": "Interrupted",
    "pending": "Waiting",
}

#: The ClaimLens mark: a lens over a play triangle, with the check that stands for the
#: source review. Drawn on a 24 grid with `currentColor`, so the same body serves the
#: gradient tile in the header and the favicon.
MARK_ATTRS = (
    'fill="none" stroke="currentColor" stroke-width="1.8" '
    'stroke-linecap="round" stroke-linejoin="round"'
)
MARK_BODY = (
    '<circle cx="9.8" cy="9.8" r="8.2"/>'
    '<path d="m16 15.8 6.2 5.5"/>'
    '<path d="m11 13.6 1.6 1.6 2.8-3.4"/>'
    '<path d="M7 6.2 12 9.1 7 12Z" fill="#e5231b" stroke="#e5231b" stroke-width="1.5"/>'
)
LOGO_MARK = f'<svg viewBox="0 0 24 24" {MARK_ATTRS} aria-hidden="true">{MARK_BODY}</svg>'
#: The same mark on its brand tile, inlined so the tab icon costs no extra request.
FAVICON_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">'
    '<defs><linearGradient id="m" x1="0" y1="0" x2="1" y2="1">'
    '<stop offset="0" stop-color="#0b7d8c"/><stop offset="1" stop-color="#0a6270"/>'
    "</linearGradient></defs>"
    '<rect width="32" height="32" rx="7" fill="url(#m)"/>'
    f'<g color="#ffffff" {MARK_ATTRS} transform="translate(3.2 3.2) scale(1.067)">'
    f"{MARK_BODY}</g></svg>"
)
FAVICON_DATA_URI = "data:image/svg+xml," + quote(FAVICON_SVG, safe="")

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
  padding:0 24px; height:72px; background:var(--surface); border-bottom:1px solid var(--line);
  position:sticky; top:0; z-index:20; }
.brand { display:flex; align-items:center; gap:10px; font-weight:700; font-size:17px;
  letter-spacing:-.02em; color:var(--ink); text-decoration:none; }
/* The mark carries the brand, so it is 1.8x its first size (30px -> 54px). The bar grew
   with it and wraps on a phone, so nothing else in the top bar had to give way. */
.brand .mark { width:54px; height:54px; border-radius:16px; display:grid; place-items:center;
  background:linear-gradient(150deg,var(--accent),var(--accent-2)); color:#fff; flex:none; }
.brand .mark svg { width:40px; height:40px; }
.navlinks { display:flex; align-items:center; gap:6px; }
.navlinks a { color:var(--ink-2); text-decoration:none; font-weight:500; font-size:14px;
  padding:7px 12px; border-radius:8px; }
.navlinks a:hover { background:var(--surface-2); color:var(--ink); }
.navlinks a.active { color:var(--accent-2); background:var(--accent-wash); }
.navlinks a:focus-visible, .brand:focus-visible { outline:2px solid var(--accent);
  outline-offset:2px; border-radius:8px; }
.navuser { display:flex; align-items:center; gap:12px; }
.navuser .who { font-size:13px; color:var(--muted); }
.avatar { width:30px; height:30px; border-radius:50%; background:var(--accent-wash);
  color:var(--accent-2); display:grid; place-items:center; font-weight:700; font-size:13px; }
main { max-width:1320px; margin:0 auto; padding:34px 24px 80px; }
.page-head { margin-bottom:24px; }
.page-head h1 { font-size:26px; }
.page-head p { color:var(--muted); margin:6px 0 0; }
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
.auth-wrap { min-height:calc(100vh - 72px); display:grid; place-items:center; padding:40px 20px; }
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
.workspace { display:grid; grid-template-columns:minmax(0,1fr); gap:24px; align-items:start; }
.workspace-main { min-width:0; }
.workspace-brief { min-width:0; }
.workspace-brief:empty { display:none; }
.workspace.complete { gap:16px; }
.workspace.complete .card-head { padding:12px 16px; }
.workspace.complete .card-body { padding:12px 16px; }
.workspace-complete-note { margin:0; color:var(--muted); font-size:13px; }
.recall summary { cursor:pointer; list-style:none; }
.recall summary::-webkit-details-marker { display:none; }
.recall-hint { font-size:12px; font-weight:600; color:var(--accent-2); white-space:nowrap; }
.version { font-size:11px; font-weight:700; letter-spacing:.02em; color:var(--accent-2);
  background:var(--accent-wash); border-radius:999px; padding:2px 8px; margin-left:2px; }
.brief { max-width:70ch; }
.brief .brief-kicker { font-size:11px; font-weight:700; letter-spacing:.08em;
  text-transform:uppercase; color:var(--accent-2); margin:0 0 6px; }
.brief .brief-title { font-size:22px; line-height:1.25; margin:0 0 18px;
  padding-bottom:12px; border-bottom:1px solid var(--line-2); overflow-wrap:anywhere; }
.brief .brief-section { font-size:16px; margin:22px 0 8px; }
.brief .brief-claim { font-size:14.5px; margin:20px 0 6px; }
.brief .brief-subhead { font-size:12px; font-weight:700; letter-spacing:.05em;
  text-transform:uppercase; color:var(--muted); margin:16px 0 6px; }
.brief p { color:var(--ink-2); margin:0 0 10px; overflow-wrap:anywhere; }
.brief ul.brief-list { margin:0 0 12px; padding-left:18px; color:var(--ink-2); }
.brief ul.brief-list li { margin:4px 0; }
.brief ul.brief-list li.sub { list-style:none; margin-left:-4px; color:var(--muted);
  font-size:13.5px; }
.claim-signals { display:flex; flex-wrap:wrap; gap:6px; list-style:none; padding:0;
  margin:0 0 12px; }
.claim-signals .signal { display:inline-flex; align-items:center; gap:6px; font-size:12px;
  font-weight:600; padding:3px 10px; border-radius:999px; background:var(--surface-2);
  color:var(--ink-2); border:1px solid var(--line-2); }
.claim-signals .signal::before { content:""; width:8px; height:8px; flex:none;
  background:currentColor; }
.claim-signals .supporting { color:var(--ok); background:var(--ok-wash); }
.claim-signals .supporting::before { clip-path:polygon(50% 0,100% 100%,0 100%); }
.claim-signals .contradicting { color:var(--bad); background:var(--bad-wash); }
.claim-signals .contradicting::before { clip-path:polygon(50% 100%,100% 0,0 0); }
.claim-signals .verdict::before { border-radius:50%; }
.claim-signals .verdict.ok { color:var(--ok); background:var(--ok-wash); }
.claim-signals .verdict.bad { color:var(--bad); background:var(--bad-wash); }
.claim-signals .verdict.warn { color:var(--warn); background:var(--warn-wash); }
.claim-signals .verdict.idle { color:var(--muted); }
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
/* Says out loud that the view stopped updating itself, instead of looking merely quiet. */
.connection { margin:0; font-size:12.5px; font-weight:600; color:var(--warn);
  background:var(--warn-wash); border-radius:999px; padding:3px 10px; }
.connection[hidden] { display:none; }
.transcript { white-space:pre-wrap; overflow-wrap:anywhere; font-family:var(--mono);
  font-size:13px; line-height:1.65; color:var(--ink-2); margin:0; }
.card-actions { display:flex; align-items:center; gap:8px; flex-wrap:wrap; }
.history-actions { display:flex; align-items:center; gap:8px; flex-wrap:wrap; }
.history-list { display:grid; gap:8px; }
.history-row { display:flex; align-items:center; justify-content:space-between; gap:12px;
  padding:12px 4px;
  border-bottom:1px solid var(--line-2); }
.history-row:last-child { border-bottom:0; }
.history-row a { font-weight:600; text-decoration:none; }
.history-title { display:block; color:var(--ink-2); font-size:13.5px; margin-top:3px; }
.history-row small { display:block; color:var(--muted); margin-top:3px; }
.history-filter { max-width:170px; min-height:34px; padding:6px 9px; font-size:13px; }
.history-row[aria-current] { background:var(--accent-wash); border-radius:var(--radius-sm);
  padding-left:10px; padding-right:10px; }
.history-more { margin-top:6px; }
.history-more summary { cursor:pointer; color:var(--accent); font-weight:600; font-size:13px;
  padding:8px 4px; }
.launcher summary { cursor:pointer; font-weight:600; font-size:14px; padding:16px 20px;
  color:var(--ink-2); }
.launcher[open] summary { padding-bottom:0; }
.check { display:flex; align-items:flex-start; gap:10px; margin-top:14px; font-size:13.5px;
  color:var(--ink-2); }
.check input { margin:2px 0 0; width:16px; height:16px; accent-color:var(--accent); flex:0 0 auto; }
.check small { display:block; color:var(--muted); font-size:12.5px; margin-top:2px; }
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
/* Desktop reads the run and the brief side by side; anything narrower stacks them,
   so no layout ever needs horizontal scrolling. */
@media (min-width:1080px) {
  .workspace { grid-template-columns:minmax(0,1fr) minmax(0,1.05fr); }
  .workspace.complete { grid-template-columns:minmax(0,1fr); }
  .report { margin:0; }
}
@media (max-width:720px) {
  /* The bar wraps rather than scrolls sideways, so version and Recent analyses stay
     reachable on a phone and by keyboard in the same order as on desktop. */
  nav.app { flex-wrap:wrap; height:auto; gap:8px; padding:10px 14px; }
  .navlinks { order:3; width:100%; }
  .navlinks a { padding:8px 10px; }
  .workspace { gap:16px; }
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

#: Appended to `STYLES` for the exported brief: no app chrome, and it prints as a document.
STANDALONE_BRIEF_STYLES = """
body { background:var(--surface); }
main { padding:32px 20px 56px; }
.report { box-shadow:none; border:0; }
.report .card-body { padding:0; }
.brief { max-width:none; }
@media print {
  :root { color-scheme:light; }
  body { background:#fff; }
  main { padding:0; max-width:none; }
  a { color:inherit; text-decoration:underline; }
  .brief .brief-title, .brief .brief-section, .brief .brief-claim { break-after:avoid; }
  .brief ul.brief-list, .claim-signals { break-inside:avoid; }
}
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
  <link rel="icon" type="image/svg+xml" href="{FAVICON_DATA_URI}">
  <meta name="theme-color" content="#0b7d8c">
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
    server = build_web_server(config, host=host, port=port)
    print(f"ClaimLens process page: http://{host}:{server.server_port}")
    server.serve_forever()


def build_web_server(config: AppConfig, *, host: str, port: int) -> ThreadingHTTPServer:
    database_path = config.paths.database
    db.init_db(database_path)
    recovered_jobs = db.recover_orphaned_jobs(database_path)
    if recovered_jobs:
        LOGGER.warning("Marked %s orphaned web jobs as interrupted", recovered_jobs)

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            query = parse_qs(parsed.query)
            run_id = _int_value(query.get("run_id", [""])[0])
            context = self._context()
            self._pending_guest_cookie = (
                None if self._cookie("claimlens_guest") else context.guest_token
            )
            if parsed.path == "/health":
                self._send_text("ok\n")
                return
            if parsed.path == LIVE_STATUS_ASSET:
                # Same-origin asset: the production CSP keeps script-src 'self'.
                self._send_asset(LIVE_STATUS_JS, content_type="text/javascript; charset=utf-8")
                return
            if parsed.path == "/health/jobs":
                self._send_json(db.job_metrics(database_path))
                return
            if parsed.path == "/api/run-status":
                self._send_run_status(database_path, run_id=run_id, context=context)
                return
            if parsed.path == "/login":
                self._send_html(render_login_page(context=context))
                return
            if parsed.path == "/history":
                self._send_html(
                    render_history_page(
                        database_path,
                        user_id=context.user_id,
                        guest_token=context.guest_token,
                        context=context,
                        status_filter=query.get("status", [""])[0],
                        csrf_token=context.csrf_token,
                    )
                )
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
                    as_html=query.get("format", [""])[0] == "html",
                )
                return
            if parsed.path == "/transcript":
                status, run, transcript = resolve_transcript(
                    database_path,
                    run_id,
                    user_id=context.user_id,
                    guest_token=context.guest_token,
                )
                self._send_html(
                    render_transcript_page(
                        database_path,
                        run=run,
                        transcript=transcript,
                        context=context,
                    ),
                    status=status,
                )
                return
            if parsed.path == "/transcript/download":
                self._send_transcript_download(
                    database_path,
                    run_id=run_id,
                    context=context,
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
                briefs_path=config.paths.briefs,
            )
            self._send_html(body)

        def do_POST(self) -> None:  # noqa: N802
            context = self._context()
            self._pending_guest_cookie = (
                None if self._cookie("claimlens_guest") else context.guest_token
            )
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
                    briefs_path=config.paths.briefs,
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
                    briefs_path=config.paths.briefs,
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
                if context.user_id is None:
                    _check_rate_limit(
                        database_path,
                        f"guest-ip:{self._request_ip()}",
                        config,
                    )
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
                if action in {"close_analysis", "reopen_analysis"}:
                    run_id = self._handle_visibility_action(action, form, context)
                elif action == "create":
                    run_id = create_run(
                        database_path,
                        form.get("video_url", [""])[0],
                        # The report language is a deployment setting, not a per-run choice.
                        report_language=config.pipeline.report_language,
                        fetch_metadata=True,
                        user_id=context.user_id,
                        guest_token=None if context.user_id is not None else context.guest_token,
                        verify_sources=(
                            config.sources.advanced_source_verification
                            and form.get("verify_sources", [""])[0] == "1"
                        ),
                    )
                    # Start the chain right away: the user already asked for the analysis.
                    submit_job(
                        config,
                        database_path,
                        run_id,
                        "captions",
                        form,
                        user_id=context.user_id,
                        guest_token=context.guest_token,
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
                    job_id = submit_job(
                        config,
                        database_path,
                        run_id,
                        action,
                        form,
                        user_id=context.user_id,
                        guest_token=context.guest_token,
                    )
                    if job_id is None:
                        raise ValueError("This action is already queued or running for the run.")
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
                    briefs_path=config.paths.briefs,
                )
                self._send_html(body, status=400)
                return

            self.send_response(303)
            # Closing an analysis clears the desk, so it lands on an empty workspace.
            self.send_header("Location", f"/?run_id={run_id}" if run_id is not None else "/")
            self._set_pending_guest_cookie(config)
            self.end_headers()

        def _handle_visibility_action(
            self,
            action: str,
            form: dict[str, list[str]],
            context: WebContext,
        ) -> int | None:
            """Close or reopen one owned run, and say where the browser should land."""

            run_id = int(form.get("run_id", [""])[0])
            run = db.get_visible_pipeline_run(
                database_path,
                run_id,
                user_id=context.user_id,
                guest_token=context.guest_token,
            )
            if run is None:
                raise ValueError("Run not found.")
            if action == "reopen_analysis":
                db.reopen_pipeline_run(database_path, run_id)
                return run_id
            # Settle first: only the database can say the chain has really stopped.
            run = reconcile_run_state(database_path, run_id, source_config=config.sources) or run
            if not _run_is_closable(database_path, run):
                raise ValueError(
                    "This analysis is still working. Wait until it finishes before closing it."
                )
            db.close_pipeline_run(database_path, run_id)
            return None

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
            self._set_pending_guest_cookie(config)
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
                briefs_path=config.paths.briefs,
            )
            if payload is None:
                self._send_json({"error": "Run not found."}, status=404)
                return
            self._send_json(payload)

        def _send_asset(self, body: str, *, content_type: str) -> None:
            """Serve a shipped asset. No cookie: an asset must not mint an identity."""

            encoded = body.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(encoded)))
            # The URL carries the release version, so a cached copy cannot outlive a deploy.
            self.send_header("Cache-Control", "public, max-age=86400")
            self.end_headers()
            self.wfile.write(encoded)

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
            as_html: bool = False,
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
            if as_html:
                # A self-contained document: readable and printable with only a browser.
                data = render_standalone_brief(
                    path.read_text(encoding="utf-8"),
                    title=f"ClaimLens brief · {path.stem}",
                ).encode("utf-8")
                content_type = "text/html; charset=utf-8"
                filename = f"{path.stem}.html"
            else:
                data = path.read_bytes()
                content_type = "text/markdown; charset=utf-8"
                filename = path.name
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header(
                "Content-Disposition",
                f'attachment; filename="{filename.replace(chr(34), "")}"',
            )
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _send_transcript_download(
            self,
            database_path: Path | str,
            *,
            run_id: int | None,
            context: WebContext,
        ) -> None:
            status, run, transcript = resolve_transcript(
                database_path,
                run_id,
                user_id=context.user_id,
                guest_token=context.guest_token,
            )
            if status != 200 or transcript is None or run is None:
                self._send_html(
                    render_transcript_page(
                        database_path,
                        run=run,
                        transcript=None,
                        context=context,
                    ),
                    status=status,
                )
                return
            data = _transcript_document(transcript["text"]).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header(
                "Content-Disposition",
                f'attachment; filename="{_transcript_filename(run)}"',
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
                csrf_token=guest_csrf_token(guest_token),
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
                            csrf_token=guest_csrf_token(
                                self._cookie("claimlens_guest") or new_guest_token()
                            ),
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
            self._set_pending_guest_cookie(config)
            self.end_headers()

        def _handle_logout(self, context: WebContext) -> None:
            if context.session_token:
                db.delete_session(database_path, token_digest(context.session_token))
            self.send_response(303)
            self.send_header("Location", "/")
            self._clear_cookie("claimlens_session", config=config)
            self._set_pending_guest_cookie(config)
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
                try:
                    validate_provider_api_key(provider, key)
                except ApiKeyTestError as exc:
                    raise ValueError(str(exc)) from exc
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
                    deployment_secret=keyring_for_config(config),
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
                    deployment_secret=keyring_for_config(config),
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
                        keyring_for_config(config),
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

        def _request_ip(self) -> str:
            """Accept proxy identity only when the direct peer is explicitly trusted."""
            return resolve_request_ip(
                self.client_address[0],
                self.headers.get("X-Real-IP"),
                config.web.trusted_proxy_ips,
            )

        def _set_pending_guest_cookie(self, config: AppConfig) -> None:
            value = getattr(self, "_pending_guest_cookie", None)
            if value:
                self._set_cookie("claimlens_guest", value, config=config)
                self._pending_guest_cookie = None

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

    return ThreadingHTTPServer((host, port), Handler)


def _gated_step(step: str | None, source_config: SourceConfig | None) -> str | None:
    """Hide a step the deployment has switched off, so no view can offer it."""

    if step == "source_verification" and source_config is not None:
        return step if source_config.advanced_source_verification else None
    return step


def reconcile_run_state(
    database_path: Path | str,
    run_id: int,
    *,
    source_config: SourceConfig | None = None,
):
    """Settle a run whose stored status outlived the work that was producing it.

    A stored `running` is a claim made by a worker that may have died, or by a request
    that finished in another tab. Every read path goes through here first, so a reload
    shows what the database can actually prove rather than the last thing written.
    """

    run = db.get_pipeline_run(database_path, run_id)
    if run is None or run["status"] not in UNSETTLED_RUN_STATUSES:
        return run
    jobs = db.latest_jobs_for_run(database_path, run_id)
    if any(row["status"] in {"queued", "running"} for row in jobs):
        return run

    step_rows = db.list_run_steps(database_path, run_id)
    for row in step_rows:
        # Nothing is executing, so a step still marked running was abandoned. Leaving it
        # there would strand the run; failing it puts the retry back in the user's hands.
        if row["status"] == "running":
            db.set_step_status(
                database_path,
                run_id=run_id,
                step=row["step"],
                status="failed",
                failure_message="The step stopped before it finished. Launch it again to resume.",
            )
    statuses = {row["step"]: row["status"] for row in db.list_run_steps(database_path, run_id)}
    failed = next((step for step, status in statuses.items() if status == "failed"), None)
    if failed is not None:
        db.set_run_status(
            database_path,
            run_id=run_id,
            status="failed",
            current_step=failed,
            failure_message=run["failure_message"],
        )
        return db.get_pipeline_run(database_path, run_id)

    pending = _gated_step(next_eligible_step(database_path, run_id), source_config)
    if pending is not None:
        if run["status"] != "pending":
            db.set_run_status(
                database_path,
                run_id=run_id,
                status="pending",
                current_step=pending,
            )
        return db.get_pipeline_run(database_path, run_id)

    terminal = (
        "completed_with_warnings"
        if "completed_with_warnings" in statuses.values()
        else "succeeded"
    )
    db.set_run_status(
        database_path,
        run_id=run_id,
        status=terminal,
        current_step=run["current_step"],
    )
    return db.get_pipeline_run(database_path, run_id)


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
    briefs_path: Path | str | None = None,
) -> str:
    _ = status_filter  # The archive moved to /history; the filter lives there now.
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
    if selected_run is not None:
        selected_run = reconcile_run_state(
            database_path,
            selected_run["id"],
            source_config=source_config,
        )
    notice_html = f'<div class="notice">{html.escape(notice)}</div>' if notice else ""
    # A closed run keeps its place in the history, not on the workspace.
    closed = selected_run is not None and bool(selected_run["closed_at"])
    create_card = _create_card(
        csrf_token=csrf_token,
        source_config=source_config,
        collapsed=selected_run is not None and not closed,
    )
    active_workspace = ""
    if closed:
        active_workspace = _closed_card(selected_run, csrf_token)
    elif selected_run is not None:
        step_rows = db.list_run_steps(database_path, selected_run["id"])
        next_step = _gated_step(
            next_eligible_step(database_path, selected_run["id"]),
            source_config,
        )
        active_workspace = _active_workspace(
            database_path,
            selected_run,
            step_rows,
            next_step,
            csrf_token=csrf_token,
            user_id=user_id,
            source_config=source_config,
            briefs_path=briefs_path,
            guest_token=guest_token,
        )
    # Work in progress comes first; the launcher stays out of its way.
    sections = (
        f"{active_workspace}\n{create_card}" if selected_run is not None else create_card
    )
    body = f"""
<main>
  <div class="page-head">
    <h1>Analyses</h1>
    <p>ClaimLens turns a video link into an analysed transcript, extracted claims, and evidence
      reviews grounded in scientific publications—built mainly for science and health topics.</p>
  </div>
  {notice_html}
  {sections}
</main>
{_live_status_mount(selected_run["id"]) if selected_run is not None and not closed else ""}
"""
    return _page_shell(
        "ClaimLens Analyses",
        body,
        context=context,
        csrf_token=csrf_token,
        active="process",
    )


def render_history_page(
    database_path: Path | str,
    *,
    user_id: int | None = None,
    guest_token: str | None = None,
    context: WebContext | None = None,
    status_filter: str = "",
    csrf_token: str = "",
) -> str:
    """The archive, reachable from the top bar rather than buried under the workspace."""

    runs = (
        db.list_visible_pipeline_runs(database_path, user_id=user_id, guest_token=guest_token)
        if user_id is not None or guest_token
        else db.list_pipeline_runs(database_path)
    )
    allowed_filters = {"running", "succeeded", "failed", "completed_with_warnings"}
    if status_filter in allowed_filters:
        runs = [row for row in runs if row["status"] == status_filter]
    body = f"""
<main>
  <div class="page-head">
    <h1>Recent analyses</h1>
  </div>
  {_history_card(runs, None, status_filter, csrf_token=csrf_token)}
</main>
"""
    return _page_shell(
        "ClaimLens Recent Analyses",
        body,
        context=context,
        csrf_token=csrf_token,
        active="history",
    )


def _create_card(
    *,
    csrf_token: str,
    source_config: SourceConfig | None,
    collapsed: bool,
) -> str:
    """Render the launcher, collapsed to a disclosure once a run is on screen."""

    verify_option = ""
    if source_config is None or source_config.advanced_source_verification:
        verify_option = """
        <label class="check">
          <input type="checkbox" name="verify_sources" value="1">
          <span>Check claims against PubMed and Semantic Scholar
            <small>Runs after the brief. Slower, and needs evidence provider keys.</small></span>
        </label>
"""
    form = f"""
      <form method="post">
        <input type="hidden" name="csrf_token" value="{html.escape(csrf_token)}">
        <input type="hidden" name="action" value="create">
        <div class="row">
          <label class="field grow" style="flex:1 1 320px">
            <span>YouTube video URL</span>
            <input name="video_url" type="url" required
              placeholder="https://www.youtube.com/watch?v=...">
          </label>
          <button type="submit" class="btn btn-primary">Start analysis</button>
        </div>
        {verify_option}
      </form>
"""
    if collapsed:
        return f"""
  <div class="card">
    <details class="launcher">
      <summary>Start another analysis</summary>
      <div class="card-body">{form}</div>
    </details>
  </div>
"""
    return f"""
  <div class="card">
    <div class="card-head"><h2>New analysis</h2></div>
    <div class="card-body">{form}</div>
  </div>
"""


def _active_workspace(
    database_path: Path | str,
    selected_run,
    step_rows,
    next_step: str | None,
    *,
    csrf_token: str,
    user_id: int | None,
    source_config: SourceConfig | None,
    briefs_path: Path | str | None = None,
    guest_token: str | None = None,
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
    video_id = html.escape(selected_run["video_id"] or "")
    video_url = html.escape(selected_run["source_url"] or selected_run["video_id"] or "")
    video = db.get_video(database_path, selected_run["video_id"])
    video_title_value = (video["title"] if video is not None else None) or (
        selected_run["video_id"] or "Untitled video"
    )
    video_title = html.escape(video_title_value)
    step_rows_html = "\n".join(_step_row(row) for row in step_rows)
    # The business timeline is never behind a disclosure: it is the answer to "where is
    # my analysis". Only the row-level diagnostics fold away.
    diagnostics = f"""
    <div id="pipeline-stepper" class="stepper" aria-label="Analysis steps">{
        _stepper(step_rows)
    }</div>
    <details class="diagnostic">
      <summary>Execution details</summary>
      <div class="diagnostic-body">
        <div class="table-wrap">
          <table>
            <thead><tr><th>Step</th><th>Status</th><th>Details</th><th>Output</th></tr></thead>
            <tbody id="pipeline-steps">{step_rows_html}</tbody>
          </table>
        </div>
      </div>
    </details>
"""
    brief_html = _brief_panel(
        database_path,
        briefs_path,
        run_id=selected_run["id"],
        user_id=user_id,
        guest_token=guest_token,
    )
    # Once the brief exists, the work is complete: let it own the full reading width,
    # and fold the run identity and results behind an accessible recall control instead
    # of a permanent second column.
    if brief_html:
        outputs_html = _outputs(
            database_path, selected_run["video_id"], run_id=selected_run["id"]
        )
        return f"""
  <section class="workspace complete" aria-label="Completed analysis workspace">
    <div class="workspace-brief" id="pipeline-brief">
      <div class="card recall">
        <details>
          <summary class="card-head recall-summary">
            <div class="workspace-title"><h2>Analysis complete</h2>
              <span id="pipeline-status">{_status_badge(selected_run["status"])}</span></div>
            <span class="recall-hint">Run details</span>
          </summary>
          <div class="card-body">
            <p class="workspace-url">Video <span class="mono">{video_id}</span> · {video_title}</p>
            <p class="workspace-complete-note">The results below reflect this completed
              run.</p>
            <div id="pipeline-outputs">{outputs_html}</div>
          </div>
        </details>
      </div>
      {brief_html}
    </div>
  </section>
"""
    return f"""
  <section class="workspace" aria-label="Active analysis workspace">
    <div class="workspace-main">
      <div class="card">
        <div class="card-head">
          <div>
            <div class="workspace-title"><h2>Active analysis</h2>
              <span id="pipeline-status">{_status_badge(selected_run["status"])}</span>
              <p id="{LIVE_CONNECTION_REGION}" class="connection" role="status"
                aria-live="polite" hidden></p></div>
            <p class="workspace-url">Video <span class="mono">{video_id}</span> · {video_title}
              · {video_url}</p>
          </div>
        </div>
        <div class="card-body">
          <div class="workspace-action">
            <div id="pipeline-action">{
        _action_html(selected_run, next_step, failed_captions)
    }</div>
            <div id="pipeline-controls">{controls}</div>
            <div id="pipeline-recovery">{recovery}</div>
          </div>
          {diagnostics}
        </div>
      </div>
      <div id="pipeline-outputs">{
        _outputs(database_path, selected_run["video_id"], run_id=selected_run["id"])
    }</div>
    </div>
    <div class="workspace-brief" id="pipeline-brief">{brief_html}</div>
  </section>
"""


def _run_is_closable(database_path: Path | str, run) -> bool:
    """True once nothing in the chain can still move on its own.

    `pending` counts as working: the chain paused for the user and resumes without a new
    analysis. Only a settled run, with no queued or running job behind it, can be closed.
    """

    if run["closed_at"]:
        return False
    if run["status"] in UNSETTLED_RUN_STATUSES:
        return False
    jobs = db.latest_jobs_for_run(database_path, run["id"])
    return not any(row["status"] in LIVE_JOB_STATUSES for row in jobs)


def _close_html(database_path: Path | str, run, csrf_token: str) -> str:
    if not _run_is_closable(database_path, run):
        return ""
    return f"""
        <form method="post">
          <input type="hidden" name="csrf_token" value="{html.escape(csrf_token)}">
          <input type="hidden" name="run_id" value="{run["id"]}">
          <input type="hidden" name="action" value="close_analysis">
          <button type="submit" class="btn btn-ghost btn-sm">Close analysis</button>
        </form>
"""


def _reopen_form(run_id: int, csrf_token: str, *, label: str, css: str) -> str:
    return (
        '<form method="post">'
        f'<input type="hidden" name="csrf_token" value="{html.escape(csrf_token)}">'
        f'<input type="hidden" name="run_id" value="{run_id}">'
        '<input type="hidden" name="action" value="reopen_analysis">'
        f'<button type="submit" class="{css}">{html.escape(label)}</button>'
        "</form>"
    )


def _closed_card(selected_run, csrf_token: str) -> str:
    """What a closed run shows instead of the workspace: how to get it back."""

    reopen = _reopen_form(
        selected_run["id"],
        csrf_token,
        label="Reopen analysis",
        css="btn btn-primary",
    )
    return f"""
  <div class="card">
    <div class="card-head"><h2>Analysis closed</h2>{
        _status_badge(selected_run["status"])
    }</div>
    <div class="card-body">
      <p>Analysis #{selected_run["id"]} is closed. Nothing was deleted: it stays in
        Recent analyses with its transcript and its brief.</p>
      <div class="card-actions" style="margin-top:14px">
        {reopen}
        <a class="btn btn-ghost" href="/history">Recent analyses</a>
      </div>
    </div>
  </div>
"""


def _brief_panel(
    database_path: Path | str,
    briefs_path: Path | str | None,
    *,
    run_id: int,
    user_id: int | None,
    guest_token: str | None,
) -> str:
    """Show the finished brief beside the run, as soon as there is one to read."""

    if briefs_path is None:
        return ""
    path = _brief_path_for_run(
        database_path,
        briefs_path,
        run_id,
        user_id=user_id,
        guest_token=guest_token,
    )
    if path is None:
        return ""
    # Offset by one: the page owns the h1, and the brief's own title labels this panel.
    content = render_brief_html(path.read_text(encoding="utf-8"), heading_offset=1)
    return f"""
      <div class="card report">
        <div class="card-head"><span class="sub">Result</span>
          <div class="card-actions">
            <a href="/brief/download?run_id={run_id}&amp;format=html"
              class="btn btn-ghost btn-sm">Download HTML</a>
            <a href="/brief/download?run_id={run_id}"
              class="btn btn-ghost btn-sm">Download Markdown</a>
          </div></div>
        <div class="card-body"><article class="brief" aria-label="Analysis brief">{
        content
    }</article></div>
      </div>
"""


def _action_html(selected_run, next_step: str | None, failed_captions: bool) -> str:
    label, message = _active_action(selected_run, next_step, failed_captions)
    return f"<h3>{html.escape(label)}</h3><p>{html.escape(message)}</p>"


def _active_action(selected_run, next_step: str | None, failed_captions: bool) -> tuple[str, str]:
    if failed_captions:
        return (
            "Transcript recovery needed",
            "Captions could not be retrieved. Paste a transcript to continue.",
        )
    if next_step:
        label = _step_label(next_step)
        if selected_run["status"] == "failed":
            return (
                f"Retry: {label}",
                f"{label} did not complete. Launch it again to resume the analysis.",
            )
        return f"Next: {label}", f"Continue with {label.lower()} when you are ready."
    if selected_run["status"] in {"running", "created"}:
        return (
            "Analysis in progress",
            "ClaimLens runs the remaining steps through to the brief. This view updates itself.",
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


def _history_card(
    runs,
    selected_run_id: int | None,
    status_filter: str,
    *,
    csrf_token: str = "",
) -> str:
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
    def row_html(row) -> str:
        current = ' aria-current="true"' if row["id"] == selected_run_id else ""
        # A closed analysis is reachable in one click, so closing it costs nothing.
        actions = _status_badge(row["status"])
        if row["closed_at"]:
            actions += '<span class="badge idle">Closed</span>' + _reopen_form(
                row["id"],
                csrf_token,
                label="Reopen",
                css="btn btn-ghost btn-sm",
            )
        title = html.escape(row["video_title"] or row["video_id"] or "Untitled video")
        return (
            f'<div class="history-row"{current}><div><a href="/?run_id={row["id"]}">'
            f"{html.escape(row['video_id'] or 'Untitled analysis')}</a>"
            f'<span class="history-title">{title}</span>'
            f"<small>Analysis #{row['id']} · "
            f"{html.escape(row['started_at'] or '')}</small></div>"
            f'<div class="history-actions">{actions}</div></div>'
        )

    if not runs:
        listing = '<p class="mono">No analyses match this status.</p>'
    else:
        visible = "".join(row_html(row) for row in runs[:HISTORY_VISIBLE_ROWS])
        listing = f'<div class="history-list">{visible}</div>'
        remainder = runs[HISTORY_VISIBLE_ROWS:]
        if remainder:
            hidden = "".join(row_html(row) for row in remainder)
            listing += (
                f'<details class="history-more"><summary>Show {len(remainder)} older</summary>'
                f'<div class="history-list">{hidden}</div></details>'
            )
    return f"""
  <div class="card">
    <div class="card-head"><h2>Recent analyses</h2>
      <form method="get" class="card-actions">
        <label class="sr-only" for="status-filter">Filter analyses</label>
        <select id="status-filter" class="history-filter" name="status">{options}</select>
        <button type="submit" class="btn btn-ghost btn-sm">Filter</button></form>
    </div>
    <div class="card-body">{listing}</div>
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


def submit_job(
    config: AppConfig,
    database_path: Path | str,
    run_id: int,
    action: str,
    form: dict[str, list[str]],
    *,
    user_id: int | None = None,
    guest_token: str | None = None,
) -> int | None:
    """Queue one action and hand the whole remaining chain to a worker thread."""

    job_id = db.create_job(
        database_path,
        run_id=run_id,
        action=action,
        max_queued_jobs=config.web.max_queued_jobs,
    )
    if job_id is None:
        return None
    EXECUTOR.submit(
        _run_job,
        config,
        database_path,
        run_id,
        action,
        form,
        job_id,
        user_id,
        guest_token,
    )
    return job_id


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
    """Run one action, then keep chaining eligible steps on the same worker thread.

    Chaining in-thread rather than resubmitting keeps one worker per run, so a long
    chain cannot starve the pool of the other concurrent runs.
    """

    current_action = action
    current_job_id = job_id
    while True:
        succeeded = _execute_job(
            config,
            database_path,
            run_id,
            current_action,
            form,
            current_job_id,
            user_id=user_id,
            guest_token=guest_token,
        )
        if not succeeded:
            return
        next_action = _next_automatic_step(
            config,
            database_path,
            run_id,
            form,
            user_id=user_id,
        )
        if next_action is None:
            _mark_run_awaiting_input(config, database_path, run_id)
            return
        try:
            next_job_id = db.create_job(
                database_path,
                run_id=run_id,
                action=next_action,
                max_queued_jobs=config.web.max_queued_jobs,
            )
        except db.JobQueueFullError:
            LOGGER.info("Chain paused, queue full: run=%s next=%s", run_id, next_action)
            return
        if next_job_id is None:
            return
        db.set_run_status(
            database_path,
            run_id=run_id,
            status="running",
            current_step=next_action,
        )
        current_action = next_action
        current_job_id = next_job_id


def _next_automatic_step(
    config: AppConfig,
    database_path: Path | str,
    run_id: int,
    form: dict[str, list[str]],
    *,
    user_id: int | None,
) -> str | None:
    next_action = next_chained_step(database_path, run_id)
    if next_action == "source_verification" and not config.sources.advanced_source_verification:
        return None
    if next_action == "analysis" and not _openai_key_available(
        config,
        database_path,
        form,
        user_id=user_id,
    ):
        # Pause instead of failing: the step stays pending so the page asks for the key.
        return None
    return next_action


def _offered_step(
    config: AppConfig,
    database_path: Path | str,
    run_id: int,
) -> str | None:
    """The step the page will offer the user, applying the same gate as the renderer."""

    step = next_eligible_step(database_path, run_id)
    if step == "source_verification" and not config.sources.advanced_source_verification:
        return None
    return step


def _mark_run_awaiting_input(
    config: AppConfig,
    database_path: Path | str,
    run_id: int,
) -> None:
    """Stop claiming a run is in progress once the chain has paused for the user."""

    pending = _offered_step(config, database_path, run_id)
    if pending is None:
        return
    run = db.get_pipeline_run(database_path, run_id)
    if run is not None and run["status"] == "running":
        db.set_run_status(
            database_path,
            run_id=run_id,
            status="pending",
            current_step=pending,
        )


def _evidence_grader(
    config: AppConfig,
    database_path: Path | str,
    form: dict[str, list[str]],
    *,
    user_id: int | None,
    language: str = "en",
) -> OpenAIEvidenceGrader | None:
    """Build the grader when a key is reachable, else verify sources without grading."""

    api_key = _openai_key(config, database_path, form, user_id=user_id)
    if not api_key:
        LOGGER.info("No OpenAI key available; source verification will not grade evidence")
        return None
    return OpenAIEvidenceGrader(api_key=api_key, language=language)


def _claim_synthesizer(
    config: AppConfig,
    database_path: Path | str,
    form: dict[str, list[str]],
    *,
    user_id: int | None,
    language: str = "en",
) -> OpenAIClaimSynthesizer | None:
    """Build the synthesizer when a key is reachable; the brief degrades without it."""

    api_key = _openai_key(config, database_path, form, user_id=user_id)
    if not api_key:
        LOGGER.info("No OpenAI key available; claims will carry no evidence synthesis")
        return None
    return OpenAIClaimSynthesizer(api_key=api_key, language=language)


def _claim_translator(
    config: AppConfig,
    database_path: Path | str,
    form: dict[str, list[str]],
    *,
    user_id: int | None,
) -> OpenAIClaimTranslator | None:
    """Build the translator that puts claims into the language the indexes speak."""

    api_key = _openai_key(config, database_path, form, user_id=user_id)
    if not api_key:
        LOGGER.info("No OpenAI key available; claims will be searched as written")
        return None
    return OpenAIClaimTranslator(api_key=api_key)


def _run_language(run) -> str:
    """The language the reader asked the report in, defaulting to English."""

    try:
        return str(run["report_language"] or "en")
    except (IndexError, KeyError):
        return "en"


def _openai_key(
    config: AppConfig,
    database_path: Path | str,
    form: dict[str, list[str]],
    *,
    user_id: int | None,
) -> str | None:
    try:
        return resolve_api_key(
            database_path,
            config,
            provider="openai",
            context=KeyContext(
                user_id=user_id,
                request_keys={"openai": form.get("openai_api_key", [""])[0]},
            ),
        )
    except Exception:
        LOGGER.info("Could not resolve an OpenAI key for the evidence boundaries")
        return None


def _openai_key_available(
    config: AppConfig,
    database_path: Path | str,
    form: dict[str, list[str]],
    *,
    user_id: int | None,
) -> bool:
    try:
        return bool(
            resolve_api_key(
                database_path,
                config,
                provider="openai",
                context=KeyContext(
                    user_id=user_id,
                    request_keys={"openai": form.get("openai_api_key", [""])[0]},
                ),
            )
        )
    except Exception:
        LOGGER.info("Could not resolve an OpenAI key while chaining; pausing the run")
        return False


def _execute_job(
    config: AppConfig,
    database_path: Path | str,
    run_id: int,
    action: str,
    form: dict[str, list[str]],
    job_id: int,
    *,
    user_id: int | None,
    guest_token: str | None,
) -> bool:
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
        message = _public_error(exc)
        db.update_job(
            database_path,
            job_id=job_id,
            status="failed",
            progress=100,
            message=message,
        )
        _mark_step_failed(database_path, run_id, action, message)
        return False
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
    return True


def _mark_step_failed(
    database_path: Path | str,
    run_id: int,
    action: str,
    message: str,
) -> None:
    """Leave a failed action in a retryable state instead of stuck as running."""

    if action not in STEP_LABELS:
        return
    statuses = {row["step"]: row["status"] for row in db.list_run_steps(database_path, run_id)}
    if statuses.get(action) in {"pending", "running"}:
        db.set_step_status(
            database_path,
            run_id=run_id,
            step=action,
            status="failed",
            failure_message=message,
        )
    run = db.get_pipeline_run(database_path, run_id)
    if run is not None and run["status"] != "failed":
        db.set_run_status(
            database_path,
            run_id=run_id,
            status="failed",
            current_step=action,
            failure_message=message,
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
                request_keys={"semantic_scholar": form.get("semantic_scholar_api_key", [""])[0]},
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
            grader=_evidence_grader(
                config,
                database_path,
                form,
                user_id=user_id,
                language=_run_language(run),
            ),
            synthesizer=_claim_synthesizer(
                config,
                database_path,
                form,
                user_id=user_id,
                language=_run_language(run),
            ),
            translator=_claim_translator(config, database_path, form, user_id=user_id),
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
            source_config is None or source_config.enable_semantic_scholar
        ) and "semantic_scholar" not in saved_providers:
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
        html.escape(next_step.replace("_", " "))
    }</button>
    </form>
    """


def run_status_payload(
    database_path: Path | str,
    *,
    run_id: int,
    user_id: int | None,
    guest_token: str | None,
    csrf_token: str = "",
    source_config: SourceConfig | None = None,
    briefs_path: Path | str | None = None,
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
    # Poll and reload agree because both settle the run before reading it.
    run = reconcile_run_state(database_path, run_id, source_config=source_config) or run
    step_rows = db.list_run_steps(database_path, run_id)
    jobs = db.latest_jobs_for_run(database_path, run_id)
    next_step = _gated_step(next_eligible_step(database_path, run_id), source_config)
    captions_row = next((row for row in step_rows if row["step"] == "captions"), None)
    failed_captions = captions_row is not None and captions_row["status"] == "failed"
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
        # Work in flight. A chain briefly has none between two jobs, which is why the
        # client also keeps the active rhythm for as long as the signature keeps changing.
        "active": any(row["status"] in LIVE_JOB_STATUSES for row in jobs),
        "pipeline_status_html": _status_badge(run["status"]),
        "stepper_html": _stepper(step_rows),
        "steps_html": "\n".join(_step_row(row) for row in step_rows),
        "action_html": _action_html(run, next_step, failed_captions),
        "controls_html": _controls(
            database_path,
            run_id,
            next_step,
            csrf_token=csrf_token,
            user_id=user_id,
            source_config=source_config,
        ),
        "recovery_html": _manual_transcript_form(run_id, csrf_token) if failed_captions else "",
        "outputs_html": _outputs(database_path, run["video_id"], run_id=run_id),
        # Null rather than empty: a poll that cannot see briefs must not blank the one
        # the page already rendered.
        "brief_html": _brief_panel(
            database_path,
            briefs_path,
            run_id=run_id,
            user_id=user_id,
            guest_token=guest_token,
        )
        or None,
    }


def _live_status_mount(run_id: int) -> str:
    """Mount the tracking client and hand it this run's configuration.

    Nothing executable is inlined, so the production CSP keeps `script-src 'self'`. The
    region map travels in a data attribute, which keeps the server the only place that
    decides what a poll may repaint.
    """

    regions = html.escape(json.dumps(LIVE_REGIONS, separators=(",", ":")), quote=True)
    return f"""
<div id="live-config" hidden
  data-endpoint="/api/run-status?run_id={run_id}"
  data-regions="{regions}"
  data-connection-region="{LIVE_CONNECTION_REGION}"
  data-offline-message="{html.escape(LIVE_OFFLINE_MESSAGE, quote=True)}"
  data-active-delay="{LIVE_ACTIVE_DELAY_MS}"
  data-idle-delay="{LIVE_IDLE_DELAY_MS}"
  data-error-delay="{LIVE_ERROR_DELAY_MS}"
  data-errors-before-notice="{LIVE_ERRORS_BEFORE_NOTICE}"></div>
<script src="{LIVE_STATUS_ASSET}?v={quote(__version__)}" defer></script>
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


def _outputs(database_path: Path | str, video_id: str, *, run_id: int) -> str:
    """The deliverables of one run, as things to read rather than paths on a server."""

    cleaned = db.get_cleaned_transcript(database_path, video_id)
    brief = db.latest_brief_artifact(database_path, video_id)
    verification = db.latest_verification_run(database_path, video_id)
    video = db.get_video(database_path, video_id)
    analysis = db.latest_analysis(database_path, video_id)
    claims = db.claims_for_summary(database_path, analysis["id"]) if analysis else []
    evidence = (
        db.evidence_for_verification(database_path, verification["id"]) if verification else []
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
            "<li>Source video: "
            f'<a href="{html.escape(video["url"])}">{html.escape(video["title"])}</a></li>'
        )
    if cleaned is not None and (cleaned["text"] or "").strip():
        # The transcript is read through the app: a server path is not an action a
        # browser can take, and it is not the reader's to know.
        links.append(
            f'<li>Cleaned transcript: <a href="/transcript?run_id={run_id}">Read transcript</a> '
            f'· <a href="/transcript/download?run_id={run_id}">Download text</a></li>'
        )
    if brief is not None:
        links.append(
            f'<li>Analysis brief: <a href="/brief?run_id={run_id}">Read brief</a> '
            f'· <a href="/brief/download?run_id={run_id}&amp;format=html">Download HTML</a> '
            f'· <a href="/brief/download?run_id={run_id}">Download Markdown</a></li>'
        )
    if verification is not None:
        links.append(
            "<li>"
            f"Source verification: {html.escape(verification['status'])} "
            f"({_verification_counts(database_path, verification['id'])})"
            "</li>"
        )
    if not links:
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
        f"<span>Claims reviewed</span></div>"
        f'<div class="summary-item"><strong>{len(evidence)}</strong>'
        f"<span>Evidence snippets</span></div>"
        f'<div class="summary-item"><strong>{html.escape(report_label)}</strong>'
        f"<span>Report status</span></div></div>"
        f'<ul class="out">{"".join(links)}</ul></div></div>'
    )


def _nav(context: WebContext | None, csrf_token: str, *, active: str | None = None) -> str:
    logged_in = context is not None and context.user_id is not None
    analyses_cls = ' class="active"' if active == "process" else ""
    history_cls = ' class="active"' if active == "history" else ""
    links = f'<a href="/"{analyses_cls}>Analyses</a>'
    # The archive is a top-bar destination, not a card competing with the live run.
    links += f'<a href="/history"{history_cls}>Recent analyses</a>'
    if logged_in:
        options_cls = ' class="active"' if active == "options" else ""
        links += f'<a href="/options"{options_cls}>API keys</a>'
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
        f'<a class="brand" href="/"><span class="mark">{LOGO_MARK}</span> ClaimLens'
        f'<span class="version">v{html.escape(__version__)}</span></a>'
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
            "ClaimLens API Keys",
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
                f'Saved: <span class="mono">{html.escape(row["masked_value"])}</span>, '
                f"updated {html.escape(row['updated_at'])}"
                + (f", tested {html.escape(row['tested_at'])}" if row["tested_at"] else "")
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
    <h1>API keys</h1>
    <p>Your API keys are encrypted at rest and only power your own analyses.</p>
  </div>
  {secret_notice}
  {"".join(sections)}
  {_supadata_options_section(database_path, context)}
</main>
"""
    return _page_shell(
        "ClaimLens API Keys",
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
                <h3>{html.escape(row["label"])}</h3>
                {_status_badge(status)}
              </div>
              <div class="card-body">
                <p style="margin:0 0 12px;color:var(--muted);font-size:13.5px">
                  <span class="mono">{html.escape(row["masked_value"])}</span> · {quota}
                  · monthly native requests: {row["monthly_request_count"]}
                </p>
                <form method="post" class="row">
                  <input type="hidden" name="csrf_token" value="{csrf}">
                  <input type="hidden" name="action" value="update_supadata_key">
                  <input type="hidden" name="key_id" value="{row["id"]}">
                  <label class="field grow"><span>Label</span>
                    <input name="label" value="{html.escape(row["label"])}"></label>
                  <label class="field"><span>Priority</span>
                    <input name="priority" type="number" value="{row["priority"]}"></label>
                  <label class="check"><input name="enabled" value="1" type="checkbox" {enabled}>
                    Enabled</label>
                  <button type="submit" class="btn btn-ghost btn-sm">Update</button>
                </form>
                <div class="row" style="margin-top:12px">
                  <form method="post" style="display:inline">
                    <input type="hidden" name="csrf_token" value="{csrf}">
                    <input type="hidden" name="action" value="test_supadata_key">
                    <input type="hidden" name="key_id" value="{row["id"]}">
                    <button type="submit" class="btn btn-ghost btn-sm">Test quota</button>
                  </form>
                  <form method="post" style="display:inline">
                    <input type="hidden" name="csrf_token" value="{csrf}">
                    <input type="hidden" name="action" value="delete_supadata_key">
                    <input type="hidden" name="key_id" value="{row["id"]}">
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
    <div class="card-head"><h2>Supadata native captions</h2>{_status_badge("native")}</div>
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
        f'<td class="name">{html.escape(_step_label(row["step"]))}</td>'
        f'<td class="status">{_status_badge(row["status"])}</td>'
        f"<td>{html.escape(row['failure_message'] or '')}</td>"
        f'<td class="mono">{html.escape(_output_name(row["output_path"]))}</td>'
        "</tr>"
    )


def _output_name(output_path: str | None) -> str:
    """Name the artifact a step produced, without publishing the server's layout."""

    raw = (output_path or "").strip()
    if not raw:
        return ""
    if raw.startswith("sqlite:"):
        return raw
    return Path(raw).name


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
        content = render_brief_html(path.read_text(encoding="utf-8"))
        if run_id is not None:
            download = (
                '<div class="card-actions">'
                f'<a href="/brief/download?run_id={run_id}&amp;format=html" '
                'class="btn btn-ghost btn-sm">Download HTML</a>'
                f'<a href="/brief/download?run_id={run_id}" '
                'class="btn btn-ghost btn-sm">Download Markdown</a></div>'
            )
    body = f"""
<main>
  <div class="card report">
    <div class="card-head"><h2>Verification brief</h2>{download}</div>
    <div class="card-body"><article class="brief">{content}</article></div>
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


def resolve_transcript(
    database_path: Path | str,
    run_id: int | None,
    *,
    user_id: int | None,
    guest_token: str | None,
) -> tuple[int, object | None, object | None]:
    """Authorize a transcript request and return `(status, run, cleaned transcript)`.

    403 and 404 are kept apart on purpose: an owner who mistypes a run id learns that the
    analysis is not theirs, rather than being told it does not exist. This reveals only
    that a run id is taken, never a single word of its content.
    """

    if run_id is None:
        return 404, None, None
    if db.get_pipeline_run(database_path, run_id) is None:
        return 404, None, None
    run = db.get_visible_pipeline_run(
        database_path,
        run_id,
        user_id=user_id,
        guest_token=guest_token,
    )
    if run is None:
        return 403, None, None
    if not run["video_id"]:
        return 404, run, None
    cleaned = db.get_cleaned_transcript(database_path, run["video_id"])
    if cleaned is None or not (cleaned["text"] or "").strip():
        return 404, run, None
    return 200, run, cleaned


def render_transcript_page(
    database_path: Path | str,
    *,
    run,
    transcript,
    context: WebContext | None = None,
) -> str:
    """Read the cleaned transcript in the app, from the database rather than a path."""

    if run is None or transcript is None:
        body = """
<main>
  <div class="card">
    <div class="card-head"><h2>Transcript</h2></div>
    <div class="card-body">
      <div class="notice">No transcript is available for this analysis.</div>
    </div>
  </div>
</main>
"""
        return _page_shell(
            "ClaimLens Transcript",
            body,
            context=context,
            csrf_token=context.csrf_token if context else "",
            active="process",
            nav=context is not None,
        )
    video = db.get_video(database_path, run["video_id"])
    title = (video["title"] if video is not None else None) or run["video_id"]
    body = f"""
<main>
  <div class="card report">
    <div class="card-head">
      <div><h2>Cleaned transcript</h2>
        <span class="sub">{html.escape(title)}</span></div>
      <a class="btn btn-ghost btn-sm"
        href="/transcript/download?run_id={run["id"]}">Download text</a>
    </div>
    <div class="card-body">
      <p class="mono">Analysis #{run["id"]} · language {
        html.escape(str(run["report_language"] or "default"))
    }</p>
      <pre class="transcript">{html.escape(transcript["text"])}</pre>
    </div>
  </div>
</main>
"""
    return _page_shell(
        "ClaimLens Transcript",
        body,
        context=context,
        csrf_token=context.csrf_token if context else "",
        active="process",
        nav=context is not None,
    )


def _transcript_document(text: str) -> str:
    """One trailing newline, so the download opens cleanly in any text editor."""

    return text if text.endswith("\n") else f"{text}\n"


def _transcript_filename(run) -> str:
    video_id = re.sub(r"[^A-Za-z0-9_-]", "", str(run["video_id"] or "transcript"))
    return f"claimlens-transcript-{video_id or 'run'}-{run['id']}.txt"


def render_standalone_brief(markdown: str, *, title: str) -> str:
    """Export one brief as a self-contained HTML file.

    Everything it needs travels with it: no stylesheet request, no app chrome, and print
    rules so the same file reads on screen and on paper.
    """

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <style>{STYLES}{STANDALONE_BRIEF_STYLES}</style>
</head>
<body>
<main>
  <div class="card report">
    <div class="card-body"><article class="brief">{render_brief_html(markdown)}</article></div>
  </div>
</main>
</body>
</html>
"""


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


def render_brief_html(markdown: str, *, heading_offset: int = 0) -> str:
    """Render a stored brief as semantic HTML.

    The artifact stays Markdown so it can be downloaded unchanged; the reader gets a
    laid-out document instead of markup. Three shapes get special treatment: the product
    heading becomes a kicker above the video title, a `Signals:` bullet becomes the
    per-claim signal row, and a short line ending in a colon becomes a sub-heading.

    `heading_offset` pushes every heading down a level so the brief can be embedded under
    a page that already owns the `h1`. Styling hangs off classes, not levels.
    """

    out: list[str] = []
    in_list = False
    headings_seen = 0
    title_used = False

    def heading(level: int, css: str, text: str) -> str:
        tag = f"h{min(6, max(1, level + heading_offset))}"
        return f'<{tag} class="{css}">{_inline_html(text)}</{tag}>'

    def close_list() -> None:
        nonlocal in_list
        if in_list:
            out.append("</ul>")
            in_list = False

    for raw in markdown.splitlines():
        line = raw.strip()
        if not line:
            close_list()
            continue
        if line.startswith("#"):
            close_list()
            level = min(6, len(line) - len(line.lstrip("#")))
            text = line[level:].strip()
            headings_seen += 1
            if headings_seen == 1 and level == 1:
                out.append(f'<p class="brief-kicker">{_inline_html(text)}</p>')
                continue
            if not title_used and headings_seen == 2 and level == 2:
                title_used = True
                out.append(heading(1, "brief-title", text))
                continue
            out.append(heading(level, "brief-section" if level == 2 else "brief-claim", text))
            continue
        if line.startswith("- "):
            item = line[2:]
            indented = len(raw) - len(raw.lstrip(" ")) >= 2
            if not indented and item.startswith(SIGNALS_PREFIX):
                close_list()
                out.append(_signals_html(item[len(SIGNALS_PREFIX) :]))
                continue
            if not in_list:
                out.append('<ul class="brief-list">')
                in_list = True
            item_class = ' class="sub"' if indented else ""
            out.append(f"<li{item_class}>{_inline_html(item)}</li>")
            continue
        close_list()
        if line.endswith(":") and len(line) <= BRIEF_SUBHEAD_MAX_CHARS:
            out.append(heading(4, "brief-subhead", line[:-1]))
            continue
        out.append(f"<p>{_inline_html(line)}</p>")
    close_list()
    return "\n".join(out)


def _inline_html(text: str) -> str:
    """Escape brief text, keeping Markdown links as real links to http(s) targets."""

    parts: list[str] = []
    index = 0
    for match in MARKDOWN_LINK_RE.finditer(text):
        parts.append(html.escape(text[index : match.start()]))
        label, url = match.group(1), match.group(2)
        if url.startswith(("http://", "https://")):
            parts.append(
                f'<a href="{html.escape(url, quote=True)}" target="_blank" '
                f'rel="noopener noreferrer">{html.escape(label)}</a>'
            )
        else:
            parts.append(html.escape(match.group(0)))
        index = match.end()
    parts.append(html.escape(text[index:]))
    return "".join(parts)


def _signals_html(text: str) -> str:
    """Render the per-claim signals as labelled pills, never as icons alone."""

    items = []
    for part in text.split("·"):
        label = part.strip()
        if not label:
            continue
        lowered = label.lower()
        if lowered.startswith("verdict"):
            kind = f"verdict {_verdict_class(lowered)}"
        elif "contradicting" in lowered:
            kind = "contradicting"
        elif "supporting" in lowered:
            kind = "supporting"
        else:
            kind = "neutral"
        items.append(f'<li class="signal {kind}">{html.escape(label)}</li>')
    return f'<ul class="claim-signals">{"".join(items)}</ul>'


def _verdict_class(lowered: str) -> str:
    for verdict, css in (
        ("supported", "ok"),
        ("contradicted", "bad"),
        ("mixed", "warn"),
        ("unclear", "idle"),
        ("not_checked", "idle"),
    ):
        if verdict in lowered:
            return css
    return "idle"


def _check_rate_limit(database_path: Path | str, identity: str, config: AppConfig) -> None:
    if not db.record_rate_limit_event(
        database_path,
        identity=identity,
        window_seconds=config.web.rate_limit_window_seconds,
        max_actions=config.web.rate_limit_actions,
    ):
        raise ValueError("Too many actions submitted recently. Wait and try again.")


def resolve_request_ip(
    peer: str, forwarded_ip: str | None, trusted_proxy_ips: tuple[str, ...]
) -> str:
    """Resolve a client IP without trusting headers sent to the app directly."""
    if peer in trusted_proxy_ips and forwarded_ip and forwarded_ip.strip():
        return forwarded_ip.strip()[:128]
    return peer


def _public_error(exc: Exception) -> str:
    text = str(exc).strip()
    if not text:
        return "The action failed."
    if "/" in text or "\\" in text:
        return "The action failed. Check the application logs for details."
    return text
