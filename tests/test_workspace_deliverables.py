"""The finished analysis workspace: live tracking under CSP, deliverables, close/reopen."""

import json
import re
import shutil
import sqlite3
import subprocess
from http.client import HTTPConnection
from pathlib import Path
from threading import Thread
from urllib.request import urlopen

import pytest
from support import Client, source_config, store_cleaned_fixture

from claimlens import __version__, db
from claimlens.assets import (
    LIVE_STATUS_JS,
    claimlens_emblem_svg,
    parent_emblem_svg,
)
from claimlens.briefs import generate_brief
from claimlens.config import load_config
from claimlens.pipeline import create_run
from claimlens.web import (
    CLAIMLENS_EMBLEM_ASSET,
    CLAIMLENS_ICON_ASSET,
    LIVE_CONNECTION_REGION,
    LIVE_REGIONS,
    LIVE_STATUS_ASSET,
    PARENT_EMBLEM_ASSET,
    PARENT_SITE_LABEL,
    PARENT_SITE_URL,
    STYLES,
    WebContext,
    build_web_server,
    render_history_page,
    render_process_page,
    render_standalone_brief,
    render_transcript_page,
    resolve_transcript,
    run_status_payload,
)

VIDEO_ID = "abc123XYZ_"
VIDEO_URL = f"https://www.youtube.com/watch?v={VIDEO_ID}"


def finished_run(database, *, guest_token: str = "guest", briefs_path=None) -> int:
    """A run whose whole chain is terminal, with a transcript and a brief to read."""

    run_id = create_run(database, VIDEO_URL, guest_token=guest_token)
    store_cleaned_fixture(database, VIDEO_ID)
    db.upsert_cleaned_transcript(
        database,
        video_id=VIDEO_ID,
        transcript_id=db.get_cleaned_transcript(database, VIDEO_ID)["transcript_id"],
        text="clean text",
        output_path="/data/outputs/transcripts/abc123XYZ_.txt",
    )
    for step in ("captions", "clean_transcript", "analysis", "brief"):
        db.set_step_status(database, run_id=run_id, step=step, status="succeeded")
    db.set_run_status(database, run_id=run_id, status="succeeded", current_step="brief")
    if briefs_path is not None:
        analyze_and_brief(database, briefs_path)
    return run_id


def analyze_and_brief(database, briefs_path) -> None:
    from claimlens.analysis import analyze_cleaned_transcript

    analyze_cleaned_transcript(database, video_id=VIDEO_ID, client=Client())
    generate_brief(database, video_id=VIDEO_ID, briefs_path=briefs_path)


def serve(config):
    server = build_web_server(config, host="127.0.0.1", port=0)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def config_for(tmp_path):
    return load_config(
        env={
            "CLAIMLENS_DB": str(tmp_path / "claimlens.sqlite3"),
            "CLAIMLENS_OUTPUTS": str(tmp_path / "outputs"),
        }
    )


# --- item_087: CSP-compatible, observable tracking -----------------------------------


def test_process_page_carries_no_executable_script_of_its_own(tmp_path):
    database = tmp_path / "claimlens.sqlite3"
    run_id = create_run(database, VIDEO_URL, guest_token="guest")

    rendered = render_process_page(
        database,
        run_id=run_id,
        guest_token="guest",
        csrf_token="csrf",
    )

    # Under script-src 'self' every script must be a same-origin src, never inline code.
    for tag, body in re.findall(r"<script([^>]*)>(.*?)</script>", rendered, re.S):
        assert "src=" in tag
        assert body.strip() == ""
    assert f'<script src="{LIVE_STATUS_ASSET}?v={__version__}" defer></script>' in rendered


def test_live_client_is_served_same_origin_as_javascript(tmp_path):
    server, thread = serve(config_for(tmp_path))
    try:
        with urlopen(f"http://127.0.0.1:{server.server_port}{LIVE_STATUS_ASSET}") as response:
            body = response.read().decode("utf-8")
            assert response.headers["Content-Type"].startswith("text/javascript")
            # An asset must not mint an identity of its own.
            assert response.headers["Set-Cookie"] is None
        assert body == LIVE_STATUS_JS
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_no_page_needs_more_than_the_production_csp_allows(tmp_path):
    """Sweep every page for what `script-src 'self'` forbids.

    Inline bodies and inline event handlers both need 'unsafe-inline'; anything served from
    another host needs that host listed. The production CSP grants neither.
    """

    config = config_for(tmp_path)
    run_id = finished_run(
        config.paths.database,
        guest_token="owner",
        briefs_path=config.paths.briefs,
    )
    server, thread = serve(config)
    violations = []
    try:
        for path in (
            "/",
            f"/?run_id={run_id}",
            "/history",
            "/login",
            f"/brief?run_id={run_id}",
            f"/transcript?run_id={run_id}",
            f"/brief/download?run_id={run_id}&format=html",
        ):
            connection = HTTPConnection("127.0.0.1", server.server_port)
            connection.request("GET", path, headers={"Cookie": "claimlens_guest=owner"})
            response = connection.getresponse()
            assert response.status == 200, path
            body = response.read().decode("utf-8")
            for tag, inner in re.findall(r"<script([^>]*)>(.*?)</script>", body, re.S):
                if inner.strip():
                    violations.append((path, "inline script body"))
                source = re.search(r'src="([^"]+)"', tag)
                if source and re.match(r"https?://|//", source.group(1)):
                    violations.append((path, f"off-origin script {source.group(1)}"))
            for handler in re.findall(r'\son[a-z]+="[^"]*"', body):
                violations.append((path, f"inline handler {handler.strip()}"))
            for url in re.findall(r'(?:href|src)="((?:https?:)?//[^"]+)"', body):
                # A link to the source video or to the parent site is a destination the
                # reader chooses, not a resource the page loads.
                destinations = ("youtube.com", "youtu.be", "paulmondou.fr")
                if not any(host in url for host in destinations):
                    violations.append((path, f"off-origin resource {url}"))
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    assert violations == []


def test_live_configuration_travels_in_data_attributes(tmp_path):
    database = tmp_path / "claimlens.sqlite3"
    run_id = create_run(database, VIDEO_URL, guest_token="guest")

    rendered = render_process_page(
        database,
        run_id=run_id,
        guest_token="guest",
        csrf_token="csrf",
    )

    assert f'data-endpoint="/api/run-status?run_id={run_id}"' in rendered
    assert f'data-connection-region="{LIVE_CONNECTION_REGION}"' in rendered
    regions = json.loads(
        re.search(r'data-regions="([^"]+)"', rendered).group(1).replace("&quot;", '"')
    )
    assert regions == LIVE_REGIONS


def test_every_advertised_region_exists_and_is_filled_by_the_payload(tmp_path):
    database = tmp_path / "claimlens.sqlite3"
    run_id = finished_run(database)

    rendered = render_process_page(
        database,
        run_id=run_id,
        guest_token="guest",
        csrf_token="csrf",
    )
    payload = run_status_payload(
        database,
        run_id=run_id,
        user_id=None,
        guest_token="guest",
        csrf_token="csrf",
    )

    for region, key in LIVE_REGIONS.items():
        assert f'id="{region}"' in rendered
        assert key in payload


def test_the_page_reserves_a_place_to_announce_lost_updates(tmp_path):
    database = tmp_path / "claimlens.sqlite3"
    run_id = create_run(database, VIDEO_URL, guest_token="guest")

    rendered = render_process_page(
        database,
        run_id=run_id,
        guest_token="guest",
        csrf_token="csrf",
    )

    assert f'id="{LIVE_CONNECTION_REGION}"' in rendered
    assert 'aria-live="polite"' in rendered
    # The client announces only after repeated failures, and takes it back on success.
    assert "ERRORS_BEFORE_NOTICE" in LIVE_STATUS_JS
    assert "announce(false)" in LIVE_STATUS_JS


def test_a_job_handoff_keeps_the_active_poll_rhythm(tmp_path):
    """No queued job for a moment, but the state moved, so the client stays fast."""

    database = tmp_path / "claimlens.sqlite3"
    run_id = create_run(database, VIDEO_URL, guest_token="guest")
    job_id = db.create_job(database, run_id=run_id, action="captions")
    before = run_status_payload(database, run_id=run_id, user_id=None, guest_token="guest")

    # The worker finishes one step before it queues the next: nothing is in flight here.
    db.set_step_status(database, run_id=run_id, step="captions", status="succeeded")
    db.update_job(database, job_id=job_id, status="succeeded")
    handoff = run_status_payload(database, run_id=run_id, user_id=None, guest_token="guest")

    assert before["active"] is True
    assert handoff["active"] is False
    # The signature moved, and the client reads a change as a reason to poll fast again.
    assert handoff["signature"] != before["signature"]
    assert "state.active || changed ? ACTIVE_DELAY : IDLE_DELAY" in LIVE_STATUS_JS


@pytest.mark.skipif(shutil.which("node") is None, reason="node is needed to run the client")
def test_the_client_itself_polls_paints_announces_and_recovers(tmp_path):
    """Execute the shipped client, rather than only reading it.

    There is no browser here, so the harness gives the real asset a minimal DOM and reports
    what it did: what it painted, which rhythm it chose, and when it spoke up.
    """

    asset = tmp_path / "live-status.js"
    asset.write_text(LIVE_STATUS_JS, encoding="utf-8")
    harness = Path(__file__).parent / "live_status_harness.js"

    result = subprocess.run(
        ["node", str(harness), str(asset)],
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    )
    observed = json.loads(result.stdout)

    assert observed["endpoint"] == "/api/run-status?run_id=7"
    assert observed["painted"] == "<b>one</b>"
    assert observed["activeDelay"] == 2000
    # A hand-off reports no work in flight, yet the state moved: stay on the fast rhythm.
    assert observed["handoffDelay"] == 2000
    # Nothing queued and nothing new: only then does it back off.
    assert observed["idleDelay"] == 15000
    # One failure is noise; the second in a row is announced, and recovery is silent again.
    assert observed["afterOneError"] == {"delay": 5000, "announced": False}
    assert observed["afterTwoErrors"]["announced"] is True
    assert "unavailable" in observed["afterTwoErrors"]["message"]
    # A rejected response must not blank what the page already showed.
    assert observed["afterRejection"] == {"delay": 5000, "painted": "<b>three</b>"}
    assert observed["recovered"] == {
        "announced": False,
        "message": "",
        "painted": "<b>four</b>",
    }
    # A hidden tab waits instead of polling.
    assert observed["hiddenTab"] == {"delay": 15000, "requests": 8}


# --- item_088: a simpler bar and launcher --------------------------------------------


def test_the_brand_mark_keeps_its_tile_and_enlarges_its_contents():
    # The square remains 54px while the Icones V3 emblem fills the reserved tile.
    assert ".brand .mark { width:54px; height:54px;" in STYLES
    assert ".brand .mark img { width:100%; height:100%; object-fit:contain;" in STYLES
    # The bar wraps rather than scrolls sideways at phone width.
    assert "nav.app { flex-wrap:wrap;" in STYLES


def test_analysis_copy_and_navigation_use_the_requested_labels(tmp_path):
    database = tmp_path / "claimlens.sqlite3"
    rendered = render_process_page(database)

    assert "ClaimLens turns a video link" in rendered
    assert "Track transcript extraction" not in rendered
    assert "Runs through to the brief on its own" not in rendered


# --- item_099: the account avatar gives way to the parent site link ------------------


def signed_in(email: str = "reader@example.test") -> WebContext:
    return WebContext(
        user_id=7,
        email=email,
        csrf_token="csrf",
        guest_token="guest",
        session_token="session",
    )


def test_signed_in_bar_swaps_the_account_avatar_for_the_parent_link(tmp_path):
    database = tmp_path / "claimlens.sqlite3"

    rendered = render_process_page(database, csrf_token="csrf", context=signed_in())

    # The initial pastille is gone, not merely hidden.
    assert 'class="avatar"' not in rendered
    assert ">R</span>" not in rendered
    # Exactly one way out, at the corner the avatar used to hold.
    assert rendered.count('class="parent-link"') == 1
    assert f'href="{PARENT_SITE_URL}"' in rendered
    assert f'src="{PARENT_EMBLEM_ASSET}?v={__version__}"' in rendered
    # The session controls the avatar sat beside are untouched.
    assert "reader@example.test" in rendered
    assert 'name="action" value="logout"' in rendered


def test_the_parent_link_navigates_in_place_and_announces_its_destination(tmp_path):
    database = tmp_path / "claimlens.sqlite3"

    rendered = render_process_page(database, csrf_token="csrf", context=signed_in())
    link = re.search(r"<a class=\"parent-link\"[^>]*>", rendered).group(0)

    # Leaving for the parent site replaces this page instead of spawning a tab, so Back
    # brings the reader home. With no second window, `noopener` has nothing to protect.
    assert "target=" not in link
    assert "rel=" not in link
    # The name says the destination; the image is decorative beside it.
    assert f'aria-label="{PARENT_SITE_LABEL}"' in link
    assert 'alt=""' in rendered[rendered.index(link) :]
    assert ".navuser .parent-link:focus-visible { outline:2px solid var(--accent);" in STYLES


def test_the_parent_link_holds_a_stable_square_at_every_width():
    # Reserved before the PNG decodes, so nothing in the bar shifts on load.
    assert ".navuser .parent-link { display:grid; place-items:center; width:30px;" in STYLES
    assert "height:30px;\n  flex:none;" in STYLES
    # The emblem keeps its own proportions inside that square.
    assert ".navuser .parent-link img { width:100%; height:100%; object-fit:contain;" in STYLES
    # At phone width the e-mail is what gives way, so the link stays reachable.
    assert ".navuser .who { display:none; }" in STYLES


def test_guest_bar_keeps_login_and_offers_the_same_parent_link(tmp_path):
    database = tmp_path / "claimlens.sqlite3"

    rendered = render_process_page(database, csrf_token="csrf", guest_token="guest")

    assert 'href="/login"' in rendered
    assert 'class="avatar"' not in rendered
    # A guest reaches the parent site from the same corner, on the same terms.
    assert rendered.count('class="parent-link"') == 1
    assert f'href="{PARENT_SITE_URL}"' in rendered
    assert f'aria-label="{PARENT_SITE_LABEL}"' in rendered


def test_the_parent_link_is_the_only_off_origin_destination_the_bar_offers(tmp_path):
    database = tmp_path / "claimlens.sqlite3"

    for rendered in (
        render_process_page(database, csrf_token="csrf", context=signed_in()),
        render_process_page(database, csrf_token="csrf", guest_token="guest"),
    ):
        bar = re.search(r"<nav class=\"app\">.*?</nav>", rendered, re.S).group(0)
        off_origin = re.findall(r'href="((?:https?:)?//[^"]*)"', bar)
        assert off_origin == [PARENT_SITE_URL]


def test_the_claimlens_brand_assets_are_served_same_origin(tmp_path):
    server, thread = serve(config_for(tmp_path))
    try:
        for asset in (CLAIMLENS_ICON_ASSET, CLAIMLENS_EMBLEM_ASSET):
            url = f"http://127.0.0.1:{server.server_port}{asset}"
            with urlopen(url) as response:
                assert response.read() == claimlens_emblem_svg()
                assert response.headers["Content-Type"] == "image/svg+xml"
                assert response.headers["Set-Cookie"] is None
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    assert claimlens_emblem_svg().startswith(b"<svg")


def test_the_parent_emblem_is_served_same_origin_from_icones_v3(tmp_path):
    server, thread = serve(config_for(tmp_path))
    try:
        with urlopen(f"http://127.0.0.1:{server.server_port}{PARENT_EMBLEM_ASSET}") as response:
            body = response.read()
            assert response.headers["Content-Type"] == "image/svg+xml"
            # An asset must not mint an identity of its own.
            assert response.headers["Set-Cookie"] is None
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    assert body == parent_emblem_svg()
    assert body.startswith(b"<svg")
    assert b'viewBox="0 0 1024 1024"' in body


def test_recent_analyses_shows_the_video_title_after_its_identifier(tmp_path):
    database = tmp_path / "claimlens.sqlite3"
    run_id = create_run(database, VIDEO_URL, guest_token="guest")

    rendered = render_history_page(database, guest_token="guest")

    assert f'href="/?run_id={run_id}"' in rendered
    assert (
        f'<a class="history-primary" href="/?run_id={run_id}">'
        f'<span class="history-title">{VIDEO_ID}</span></a>'
        f"<small>Analysis #{run_id}" in rendered
    )


def test_recent_analyses_falls_back_to_the_identifier_without_title_metadata(tmp_path):
    from claimlens.pipeline import MANUAL_CHANNEL_ID
    from claimlens.youtube import YouTubeVideo

    database = tmp_path / "claimlens.sqlite3"
    run_id = create_run(database, VIDEO_URL, guest_token="guest")
    db.upsert_video(
        database,
        channel_id=MANUAL_CHANNEL_ID,
        video=YouTubeVideo(id=VIDEO_ID, title="", url=VIDEO_URL),
    )

    rendered = render_history_page(database, guest_token="guest")

    assert f'href="/?run_id={run_id}"' in rendered
    # No real title is on record: the title line gracefully falls back to the identifier.
    assert (
        f'<a class="history-primary" href="/?run_id={run_id}">'
        f'<span class="history-title">{VIDEO_ID}</span></a>' in rendered
    )
    assert '<span class="history-separator">:</span>' not in rendered


def test_recent_analyses_shows_a_distinct_title_independently_of_the_identifier(tmp_path):
    from claimlens.pipeline import MANUAL_CHANNEL_ID
    from claimlens.youtube import YouTubeVideo

    database = tmp_path / "claimlens.sqlite3"
    run_id = create_run(database, VIDEO_URL, guest_token="guest")
    db.upsert_video(
        database,
        channel_id=MANUAL_CHANNEL_ID,
        video=YouTubeVideo(id=VIDEO_ID, title="A real video title", url=VIDEO_URL),
    )

    rendered = render_history_page(database, guest_token="guest")

    assert f'href="/?run_id={run_id}"' in rendered
    assert (
        f'<span class="history-code">{VIDEO_ID}</span>'
        '<span class="history-separator">:</span>'
        '<span class="history-title">A real video title</span>' in rendered
    )
    assert ".history-title { color:var(--ink); font-size:15.5px; font-weight:700; }" in rendered


def test_the_empty_landing_launcher_has_no_isolated_heading_column(tmp_path):
    database = tmp_path / "claimlens.sqlite3"
    db.init_db(database)

    rendered = render_process_page(database, csrf_token="csrf")

    # The heading closes its own card-head before the form's card-body opens, so the
    # two are stacked (not flex siblings sharing one unclosed .card-head).
    assert '<div class="card-head"><h2>New analysis</h2></div>' in rendered
    assert rendered.count('<div class="card-head"><h2>New analysis</h2>\n    <div') == 0


def test_start_another_analysis_reuses_the_same_full_width_form(tmp_path):
    database = tmp_path / "claimlens.sqlite3"
    run_id = create_run(database, VIDEO_URL, guest_token="guest")
    for step in ("captions", "clean_transcript", "analysis", "brief"):
        db.set_step_status(database, run_id=run_id, step=step, status="succeeded")
    db.set_run_status(database, run_id=run_id, status="succeeded", current_step="brief")

    rendered = render_process_page(
        database, run_id=run_id, guest_token="guest", csrf_token="csrf"
    )

    assert "Start another analysis" in rendered
    assert '<div class="card-head"><h2>New analysis</h2></div>' not in rendered
    # Both entry states share the exact same form markup.
    assert 'placeholder="https://www.youtube.com/watch?v=..."' in rendered


def test_the_launcher_no_longer_asks_for_a_report_language(tmp_path):
    database = tmp_path / "claimlens.sqlite3"
    db.init_db(database)

    rendered = render_process_page(
        database,
        csrf_token="csrf",
        source_config=source_config(advanced=True),
    )

    assert "report_language" not in rendered
    assert "Report language" not in rendered


def test_a_new_analysis_uses_the_configured_report_language(tmp_path):
    config = config_for(tmp_path)
    object.__setattr__(config.pipeline, "report_language", "fr")
    server, thread = serve(config)
    try:
        connection = HTTPConnection("127.0.0.1", server.server_port)
        connection.request("GET", "/")
        response = connection.getresponse()
        response.read()
        cookie = response.headers["Set-Cookie"].split(";")[0]
        guest_token = cookie.split("=", 1)[1]
        from claimlens.auth import guest_csrf_token

        # A submitted form cannot carry a language: the field no longer exists.
        connection.request(
            "POST",
            "/",
            body=(
                f"csrf_token={guest_csrf_token(guest_token)}&action=create"
                f"&video_url=https%3A%2F%2Fwww.youtube.com%2Fwatch%3Fv%3D{VIDEO_ID}"
                "&report_language=de"
            ),
            headers={"Content-Type": "application/x-www-form-urlencoded", "Cookie": cookie},
        )
        response = connection.getresponse()
        response.read()
        assert response.status == 303
        run = db.list_pipeline_runs(config.paths.database)[0]
        assert run["report_language"] == "fr"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


# --- item_089: readable deliverables --------------------------------------------------


def test_outputs_offer_readable_links_and_no_server_path(tmp_path):
    database = tmp_path / "claimlens.sqlite3"
    briefs = tmp_path / "briefs"
    run_id = finished_run(database, briefs_path=briefs)

    rendered = render_process_page(
        database,
        run_id=run_id,
        guest_token="guest",
        csrf_token="csrf",
        briefs_path=briefs,
    )

    assert f'href="/transcript?run_id={run_id}"' in rendered
    assert f'href="/transcript/download?run_id={run_id}"' in rendered
    assert f'href="/brief/download?run_id={run_id}&amp;format=html"' in rendered
    assert "Read transcript" in rendered
    assert "Download HTML" in rendered
    # No absolute server path is ever offered as something to click or copy.
    assert "/data/outputs" not in rendered
    assert str(tmp_path) not in rendered


def test_transcript_access_separates_missing_from_not_yours(tmp_path):
    database = tmp_path / "claimlens.sqlite3"
    run_id = finished_run(database, guest_token="owner")

    assert resolve_transcript(database, run_id, user_id=None, guest_token="owner")[0] == 200
    assert resolve_transcript(database, run_id, user_id=None, guest_token="stranger")[0] == 403
    assert resolve_transcript(database, run_id + 99, user_id=None, guest_token="owner")[0] == 404
    assert resolve_transcript(database, None, user_id=None, guest_token="owner")[0] == 404


def test_a_run_without_a_cleaned_transcript_is_a_404(tmp_path):
    database = tmp_path / "claimlens.sqlite3"
    run_id = create_run(database, VIDEO_URL, guest_token="owner")

    status, run, transcript = resolve_transcript(
        database,
        run_id,
        user_id=None,
        guest_token="owner",
    )

    assert (status, transcript) == (404, None)
    assert "No transcript is available" in render_transcript_page(
        database,
        run=run,
        transcript=None,
    )


def test_the_transcript_page_reads_the_stored_text(tmp_path):
    database = tmp_path / "claimlens.sqlite3"
    run_id = finished_run(database, guest_token="owner")
    _, run, transcript = resolve_transcript(database, run_id, user_id=None, guest_token="owner")

    rendered = render_transcript_page(database, run=run, transcript=transcript)

    assert "clean text" in rendered
    assert f'href="/transcript/download?run_id={run_id}"' in rendered
    assert "/data/outputs" not in rendered


def test_transcript_download_is_plain_text_and_authorized(tmp_path):
    config = config_for(tmp_path)
    run_id = finished_run(config.paths.database, guest_token="owner")
    server, thread = serve(config)
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        connection = HTTPConnection("127.0.0.1", server.server_port)
        connection.request(
            "GET",
            f"/transcript/download?run_id={run_id}",
            headers={"Cookie": "claimlens_guest=owner"},
        )
        response = connection.getresponse()
        body = response.read().decode("utf-8")
        assert response.status == 200
        assert response.headers["Content-Type"] == "text/plain; charset=utf-8"
        assert "attachment" in response.headers["Content-Disposition"]
        assert f"{VIDEO_ID}-{run_id}.txt" in response.headers["Content-Disposition"]
        assert body == "clean text\n"

        connection.request(
            "GET",
            f"/transcript/download?run_id={run_id}",
            headers={"Cookie": "claimlens_guest=stranger"},
        )
        forbidden = connection.getresponse()
        forbidden.read()
        assert forbidden.status == 403
        assert base  # the server answered on its own origin
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_the_html_export_is_a_self_contained_document():
    exported = render_standalone_brief(
        "# ClaimLens\n\n## A video title\n\n- A key point\n",
        title="ClaimLens brief",
    )

    assert exported.startswith("<!doctype html>")
    assert "A video title" in exported
    # Self-contained: styles inline, and nothing to fetch from anywhere.
    assert "<style>" in exported
    assert "src=" not in exported
    assert 'href="http' not in exported
    assert "@media print" in exported


def test_brief_download_serves_html_or_markdown_on_request(tmp_path):
    config = config_for(tmp_path)
    run_id = finished_run(
        config.paths.database,
        guest_token="owner",
        briefs_path=config.paths.briefs,
    )
    server, thread = serve(config)
    try:
        connection = HTTPConnection("127.0.0.1", server.server_port)
        connection.request(
            "GET",
            f"/brief/download?run_id={run_id}&format=html",
            headers={"Cookie": "claimlens_guest=owner"},
        )
        response = connection.getresponse()
        body = response.read().decode("utf-8")
        assert response.status == 200
        assert response.headers["Content-Type"] == "text/html; charset=utf-8"
        assert response.headers["Content-Disposition"].endswith('.html"')
        assert body.startswith("<!doctype html>")

        connection.request(
            "GET",
            f"/brief/download?run_id={run_id}",
            headers={"Cookie": "claimlens_guest=owner"},
        )
        markdown = connection.getresponse()
        raw = markdown.read().decode("utf-8")
        assert markdown.headers["Content-Type"] == "text/markdown; charset=utf-8"
        assert raw.startswith("#")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


# --- item_090: close and reopen -------------------------------------------------------


def test_a_finished_analysis_is_compact_and_has_no_close_control(tmp_path):
    database = tmp_path / "claimlens.sqlite3"
    briefs = tmp_path / "briefs"
    run_id = finished_run(database, briefs_path=briefs)

    rendered = render_process_page(
        database,
        run_id=run_id,
        guest_token="guest",
        csrf_token="csrf",
        briefs_path=briefs,
    )

    assert 'value="close_analysis"' not in rendered
    assert "Close analysis" not in rendered
    assert '<section class="workspace complete"' in rendered
    assert '<details class="workspace-details">' in rendered
    assert "Execution details" in rendered


def test_an_unfinished_analysis_cannot_be_closed(tmp_path):
    database = tmp_path / "claimlens.sqlite3"
    run_id = create_run(database, VIDEO_URL, guest_token="guest")
    db.create_job(database, run_id=run_id, action="captions")
    db.set_run_status(database, run_id=run_id, status="running", current_step="captions")

    rendered = render_process_page(
        database,
        run_id=run_id,
        guest_token="guest",
        csrf_token="csrf",
    )

    assert "close_analysis" not in rendered


def test_a_run_paused_for_the_user_is_still_working(tmp_path):
    """`pending` means the chain waits for input, not that the analysis is over."""

    database = tmp_path / "claimlens.sqlite3"
    run_id = create_run(database, VIDEO_URL, guest_token="guest")
    db.set_step_status(database, run_id=run_id, step="captions", status="succeeded")
    db.set_run_status(database, run_id=run_id, status="pending", current_step="clean_transcript")

    rendered = render_process_page(
        database,
        run_id=run_id,
        guest_token="guest",
        csrf_token="csrf",
    )

    assert "close_analysis" not in rendered


def test_closing_hides_the_workspace_and_keeps_everything(tmp_path):
    database = tmp_path / "claimlens.sqlite3"
    briefs = tmp_path / "briefs"
    run_id = finished_run(database, briefs_path=briefs)

    db.close_pipeline_run(database, run_id)
    rendered = render_process_page(
        database,
        run_id=run_id,
        guest_token="guest",
        csrf_token="csrf",
        briefs_path=briefs,
    )

    assert "Analysis closed" in rendered
    assert "Active analysis" not in rendered
    assert 'value="reopen_analysis"' in rendered
    # Closing hides; it never deletes. The launcher is open for the next analysis.
    assert db.get_pipeline_run(database, run_id) is not None
    assert db.get_cleaned_transcript(database, VIDEO_ID) is not None
    assert db.latest_brief_artifact(database, VIDEO_ID) is not None
    assert "New analysis" in rendered
    # Nothing left to poll for a closed run.
    assert LIVE_STATUS_ASSET not in rendered


def test_recent_analyses_keeps_a_closed_run_and_offers_to_reopen_it(tmp_path):
    database = tmp_path / "claimlens.sqlite3"
    run_id = finished_run(database)
    db.close_pipeline_run(database, run_id)

    rendered = render_history_page(
        database,
        guest_token="guest",
        status_filter="",
        csrf_token="csrf",
    )

    assert f'href="/?run_id={run_id}"' in rendered
    assert "Closed" in rendered
    assert 'value="reopen_analysis"' in rendered


def test_reopening_brings_the_result_back_to_the_workspace(tmp_path):
    database = tmp_path / "claimlens.sqlite3"
    briefs = tmp_path / "briefs"
    run_id = finished_run(database, briefs_path=briefs)
    db.close_pipeline_run(database, run_id)

    db.reopen_pipeline_run(database, run_id)
    rendered = render_process_page(
        database,
        run_id=run_id,
        guest_token="guest",
        csrf_token="csrf",
        briefs_path=briefs,
    )

    assert "Analysis complete" in rendered
    assert "Analysis closed" not in rendered
    assert "A video title" in rendered or "Concise summary" in rendered


def test_close_and_reopen_over_http_respect_ownership(tmp_path):
    config = config_for(tmp_path)
    database = config.paths.database
    run_id = finished_run(database, guest_token="owner")
    server, thread = serve(config)
    from claimlens.auth import guest_csrf_token

    def post(action: str, token: str) -> int:
        connection = HTTPConnection("127.0.0.1", server.server_port)
        connection.request(
            "POST",
            "/",
            body=f"csrf_token={guest_csrf_token(token)}&action={action}&run_id={run_id}",
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Cookie": f"claimlens_guest={token}",
            },
        )
        response = connection.getresponse()
        response.read()
        return response.status

    try:
        # A stranger cannot touch the visibility of someone else's analysis.
        assert post("close_analysis", "stranger") == 400
        assert db.get_pipeline_run(database, run_id)["closed_at"] is None

        assert post("close_analysis", "owner") == 303
        assert db.get_pipeline_run(database, run_id)["closed_at"] is not None

        assert post("reopen_analysis", "owner") == 303
        assert db.get_pipeline_run(database, run_id)["closed_at"] is None
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_closing_a_running_analysis_is_refused_over_http(tmp_path):
    config = config_for(tmp_path)
    database = config.paths.database
    run_id = create_run(database, VIDEO_URL, guest_token="owner")
    db.create_job(database, run_id=run_id, action="captions")
    db.set_run_status(database, run_id=run_id, status="running", current_step="captions")
    server, thread = serve(config)
    from claimlens.auth import guest_csrf_token

    try:
        connection = HTTPConnection("127.0.0.1", server.server_port)
        connection.request(
            "POST",
            "/",
            body=(
                f"csrf_token={guest_csrf_token('owner')}&action=close_analysis&run_id={run_id}"
            ),
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Cookie": "claimlens_guest=owner",
            },
        )
        response = connection.getresponse()
        body = response.read().decode("utf-8")
        assert response.status == 400
        assert "still working" in body
        assert db.get_pipeline_run(database, run_id)["closed_at"] is None
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


# --- schema migration ------------------------------------------------------------------


def test_closed_at_is_added_to_an_older_pipeline_runs_table(tmp_path):
    """The migration path required before a schema version ships, on an older fixture."""

    database = tmp_path / "claimlens.sqlite3"
    db.init_db(database)
    run_id = create_run(database, VIDEO_URL, guest_token="guest")
    with sqlite3.connect(database) as connection:
        try:
            connection.execute("ALTER TABLE pipeline_runs DROP COLUMN closed_at")
        except sqlite3.OperationalError:  # pragma: no cover - old SQLite build
            pytest.skip("This SQLite build cannot drop a column")
        connection.execute(
            "UPDATE schema_metadata SET value = '7' WHERE key = 'schema_version'"
        )

    db.init_db(database)

    run = db.get_pipeline_run(database, run_id)
    assert run["closed_at"] is None
    assert run["video_id"] == VIDEO_ID
    db.close_pipeline_run(database, run_id)
    assert db.get_pipeline_run(database, run_id)["closed_at"] is not None
