import json
from dataclasses import dataclass

from support import Client, Transcript, source_config, store_cleaned_fixture

from claimlens import __version__, db
from claimlens.analysis import TranscriptAnalysis, analyze_cleaned_transcript, parse_analysis_json
from claimlens.api_keys import save_supadata_api_key
from claimlens.assets import LIVE_STATUS_JS
from claimlens.auth import hash_password
from claimlens.briefs import generate_brief, render_markdown_brief
from claimlens.config import load_config
from claimlens.pipeline import create_run, next_eligible_step
from claimlens.web import (
    FAVICON_DATA_URI,
    FAVICON_SVG,
    HISTORY_VISIBLE_ROWS,
    LIVE_STATUS_ASSET,
    LOGO_MARK,
    MARK_BODY,
    WebContext,
    _run_job,
    reconcile_run_state,
    render_brief_html,
    render_brief_page,
    render_history_page,
    render_login_page,
    render_options_page,
    render_process_page,
    run_status_payload,
)


def test_launcher_offers_source_verification_opt_in_before_the_pipeline_runs(tmp_path):
    database = tmp_path / "claimlens.sqlite3"
    db.init_db(database)

    rendered = render_process_page(
        database,
        csrf_token="csrf",
        source_config=source_config(advanced=True),
    )

    assert 'name="verify_sources"' in rendered
    assert 'type="checkbox"' in rendered
    assert "New analysis" in rendered


def test_launcher_hides_opt_in_when_verification_is_disabled(tmp_path):
    database = tmp_path / "claimlens.sqlite3"
    db.init_db(database)

    rendered = render_process_page(
        database,
        csrf_token="csrf",
        source_config=source_config(advanced=False),
    )

    assert 'name="verify_sources"' not in rendered


def test_live_client_is_mounted_even_without_an_active_job(tmp_path):
    database = tmp_path / "claimlens.sqlite3"
    run_id = create_run(database, "https://www.youtube.com/watch?v=abc123XYZ_")
    db.set_step_status(database, run_id=run_id, step="captions", status="succeeded")

    rendered = render_process_page(database, run_id=run_id, csrf_token="csrf")

    assert f'data-endpoint="/api/run-status?run_id={run_id}"' in rendered
    assert f'<script src="{LIVE_STATUS_ASSET}' in rendered
    assert "visibilitychange" in LIVE_STATUS_JS


def test_live_payload_covers_every_dynamic_region(tmp_path):
    database = tmp_path / "claimlens.sqlite3"
    run_id = create_run(
        database,
        "https://www.youtube.com/watch?v=abc123XYZ_",
        guest_token="guest",
    )
    db.set_step_status(
        database,
        run_id=run_id,
        step="captions",
        status="failed",
        failure_message="Subtitles are unavailable.",
    )
    db.create_job(database, run_id=run_id, action="captions")

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

    assert payload is not None
    # Every region the payload can patch must exist in the server-rendered page.
    for region in (
        "pipeline-status",
        "pipeline-stepper",
        "pipeline-steps",
        "pipeline-action",
        "pipeline-controls",
        "pipeline-recovery",
        "pipeline-outputs",
        "pipeline-brief",
    ):
        assert f'id="{region}"' in rendered
    # Background actions are internal plumbing and are no longer shown or announced.
    assert "Background actions" not in rendered
    assert "pipeline-jobs" not in rendered
    assert "jobs_html" not in payload
    assert "Paste a transcript fallback" in payload["recovery_html"]
    assert "Transcript recovery needed" in payload["action_html"]


def test_failed_step_is_announced_as_a_retry(tmp_path):
    database = tmp_path / "claimlens.sqlite3"
    run_id = create_run(
        database,
        "https://www.youtube.com/watch?v=abc123XYZ_",
        guest_token="guest",
    )
    db.set_step_status(database, run_id=run_id, step="captions", status="succeeded")
    db.set_step_status(
        database,
        run_id=run_id,
        step="clean_transcript",
        status="failed",
        failure_message="Subtitle cleanup produced an empty transcript.",
    )
    db.set_run_status(database, run_id=run_id, status="failed", current_step="clean_transcript")

    payload = run_status_payload(
        database,
        run_id=run_id,
        user_id=None,
        guest_token="guest",
        csrf_token="csrf",
    )

    assert payload is not None
    assert "Retry: Prepare transcript" in payload["action_html"]
    assert 'value="clean_transcript"' in payload["controls_html"]


def test_history_collapses_older_analyses(tmp_path):
    database = tmp_path / "claimlens.sqlite3"
    for index in range(HISTORY_VISIBLE_ROWS + 3):
        create_run(database, f"https://www.youtube.com/watch?v=video{index:06d}")

    rendered = render_history_page(database, csrf_token="csrf")

    assert "Show 3 older" in rendered


# The chain only advances into analysis when an OpenAI key is actually resolvable.
CHAIN_ENV = {
    "CLAIMLENS_KEY_ENCRYPTION_SECRET": "deploy-secret",
    "OPENAI_API_KEY": "test-openai-key",
}


def chain_recorder(executed: list[str], *, fail_on: str | None = None):
    def fake_run_action(
        config,
        database_path,
        run_id,
        action,
        form,
        user_id=None,
        guest_token=None,
    ):
        executed.append(action)
        if action == fail_on:
            raise RuntimeError("step blew up")
        db.set_step_status(database_path, run_id=run_id, step=action, status="succeeded")
        return None

    return fake_run_action


def test_run_job_chains_every_step_through_to_the_brief(tmp_path, monkeypatch):
    database = tmp_path / "claimlens.sqlite3"
    run_id = create_run(database, "https://www.youtube.com/watch?v=abc123XYZ_")
    config = load_config(env=CHAIN_ENV)
    executed: list[str] = []
    monkeypatch.setattr("claimlens.web._run_action", chain_recorder(executed))

    job_id = db.create_job(database, run_id=run_id, action="captions")
    _run_job(config, database, run_id, "captions", {}, job_id)

    assert executed == ["captions", "clean_transcript", "analysis", "brief"]
    assert all(job["status"] == "succeeded" for job in db.latest_jobs_for_run(database, run_id))


def test_run_job_stops_the_chain_and_leaves_the_failed_step_retryable(tmp_path, monkeypatch):
    database = tmp_path / "claimlens.sqlite3"
    run_id = create_run(database, "https://www.youtube.com/watch?v=abc123XYZ_")
    config = load_config(env=CHAIN_ENV)
    executed: list[str] = []
    monkeypatch.setattr(
        "claimlens.web._run_action",
        chain_recorder(executed, fail_on="analysis"),
    )

    job_id = db.create_job(database, run_id=run_id, action="captions")
    _run_job(config, database, run_id, "captions", {}, job_id)

    assert executed == ["captions", "clean_transcript", "analysis"]
    steps = {row["step"]: row["status"] for row in db.list_run_steps(database, run_id)}
    assert steps["analysis"] == "failed"
    assert steps["brief"] == "pending"
    run = db.get_pipeline_run(database, run_id)
    assert run["status"] == "failed"
    # The user can pick the run back up where it broke.
    assert next_eligible_step(database, run_id) == "analysis"


def test_run_job_pauses_before_analysis_when_no_openai_key_is_available(tmp_path, monkeypatch):
    """A deployment without a server key must ask for one, not fail the step."""

    database = tmp_path / "claimlens.sqlite3"
    run_id = create_run(
        database,
        "https://www.youtube.com/watch?v=abc123XYZ_",
        guest_token="guest",
    )
    config = load_config(env={"CLAIMLENS_KEY_ENCRYPTION_SECRET": "deploy-secret"})
    executed: list[str] = []
    monkeypatch.setattr("claimlens.web._run_action", chain_recorder(executed))

    job_id = db.create_job(database, run_id=run_id, action="captions")
    _run_job(config, database, run_id, "captions", {}, job_id, None, "guest")

    assert executed == ["captions", "clean_transcript"]
    steps = {row["step"]: row["status"] for row in db.list_run_steps(database, run_id)}
    assert steps["analysis"] == "pending"
    run = db.get_pipeline_run(database, run_id)
    # Waiting on the user, not pretending to still be working.
    assert run["status"] == "pending"

    payload = run_status_payload(
        database,
        run_id=run_id,
        user_id=None,
        guest_token="guest",
        csrf_token="csrf",
    )
    assert payload is not None
    assert payload["active"] is False
    assert "Next: Analyze claims" in payload["action_html"]
    assert 'name="openai_api_key"' in payload["controls_html"]


def test_run_job_resumes_the_chain_with_a_key_supplied_on_the_form(tmp_path, monkeypatch):
    database = tmp_path / "claimlens.sqlite3"
    run_id = create_run(database, "https://www.youtube.com/watch?v=abc123XYZ_")
    config = load_config(env={"CLAIMLENS_KEY_ENCRYPTION_SECRET": "deploy-secret"})
    db.set_step_status(database, run_id=run_id, step="captions", status="succeeded")
    db.set_step_status(database, run_id=run_id, step="clean_transcript", status="succeeded")
    executed: list[str] = []
    monkeypatch.setattr("claimlens.web._run_action", chain_recorder(executed))

    form = {"openai_api_key": ["sk-typed-by-the-user"], "run_id": [str(run_id)]}
    job_id = db.create_job(database, run_id=run_id, action="analysis")
    _run_job(config, database, run_id, "analysis", form, job_id)

    assert executed == ["analysis", "brief"]


def test_run_job_skips_verification_the_deployment_has_disabled(tmp_path, monkeypatch):
    database = tmp_path / "claimlens.sqlite3"
    run_id = create_run(
        database,
        "https://www.youtube.com/watch?v=abc123XYZ_",
        verify_sources=True,
    )
    config = load_config(env=CHAIN_ENV)
    assert config.sources.advanced_source_verification is False
    executed: list[str] = []
    monkeypatch.setattr("claimlens.web._run_action", chain_recorder(executed))

    job_id = db.create_job(database, run_id=run_id, action="captions")
    _run_job(config, database, run_id, "captions", {}, job_id)

    assert executed == ["captions", "clean_transcript", "analysis", "brief"]


def test_parse_analysis_json_contract():
    analysis = parse_analysis_json(
        """
        {
          "summary": "Summary",
          "key_points": ["A"],
          "notable_claims": ["B"],
          "caveats": ["C"],
          "editorial_notes": ["D"]
        }
        """
    )

    assert analysis.summary == "Summary"
    assert analysis.notable_claims == ["B"]


def test_analyze_cleaned_transcript_stores_summary_and_claims(tmp_path):
    database = tmp_path / "claimlens.sqlite3"
    run_id = create_run(database, "https://www.youtube.com/watch?v=abc123XYZ_")
    run = db.get_pipeline_run(database, run_id)
    store_cleaned_fixture(database, run["video_id"])

    summary_id = analyze_cleaned_transcript(database, video_id=run["video_id"], client=Client())

    summary = db.latest_analysis(database, run["video_id"])
    claims = db.claims_for_summary(database, summary_id)
    assert summary["summary"] == "Concise summary."
    assert claims[0]["claim"] == "Claim one"
    assert claims[0]["verdict"] == "not_checked"
    assert claims[0]["transcript_excerpt"]


def test_analyze_cleaned_transcript_bounds_long_transcripts(tmp_path):
    @dataclass(frozen=True)
    class BoundedClient:
        model: str = "test-model"

        def analyze(self, transcript_text: str) -> TranscriptAnalysis:
            assert len(transcript_text) < 1300
            assert "omitted middle transcript content" in transcript_text
            return TranscriptAnalysis(
                summary="Summary.",
                key_points=[],
                notable_claims=["opening claim"],
                caveats=[],
                editorial_notes=[],
            )

    database = tmp_path / "claimlens.sqlite3"
    run_id = create_run(database, "https://www.youtube.com/watch?v=abc123XYZ_")
    run = db.get_pipeline_run(database, run_id)
    transcript_id = db.upsert_transcript(
        database,
        Transcript(
            video_id=run["video_id"],
            source="youtube",
            language="en",
            text="opening claim " + ("middle " * 1000) + "closing claim",
            segments=[],
        ),
    )
    db.upsert_cleaned_transcript(
        database,
        video_id=run["video_id"],
        transcript_id=transcript_id,
        text="opening claim " + ("middle " * 1000) + "closing claim",
    )

    analyze_cleaned_transcript(
        database,
        video_id=run["video_id"],
        client=BoundedClient(),
        max_chars=1200,
    )
    analysis = db.latest_analysis(database, run["video_id"])
    details = json.loads(analysis["key_points_json"])
    assert any(
        "characters from the middle were omitted" in note
        for note in details["editorial_notes"]
    )


def test_render_markdown_brief_labels_source_verification():
    markdown = render_markdown_brief(
        video_id="video123",
        source_url="https://www.youtube.com/watch?v=video123",
        summary="Summary.",
        key_points=["Point"],
        notable_claims=["Claim"],
        caveats=[],
        editorial_notes=[],
    )

    assert "Source verification: Not advanced-source-verified." in markdown
    assert "Claim verdicts: Not checked in the base MVP." in markdown


def test_generate_brief_is_idempotent(tmp_path):
    database = tmp_path / "claimlens.sqlite3"
    run_id = create_run(database, "https://www.youtube.com/watch?v=abc123XYZ_")
    run = db.get_pipeline_run(database, run_id)
    store_cleaned_fixture(database, run["video_id"])
    analyze_cleaned_transcript(database, video_id=run["video_id"], client=Client())

    first = generate_brief(database, video_id=run["video_id"], briefs_path=tmp_path / "briefs")
    second = generate_brief(database, video_id=run["video_id"], briefs_path=tmp_path / "briefs")

    assert first == second
    assert first.read_text(encoding="utf-8").startswith("# ClaimLens Brief")
    assert db.latest_brief_artifact(database, run["video_id"])["path"] == str(first)


def test_render_brief_page_renders_generated_markdown(tmp_path):
    database = tmp_path / "claimlens.sqlite3"
    run_id = create_run(
        database,
        "https://www.youtube.com/watch?v=abc123XYZ_",
        report_language="fr",
    )
    run = db.get_pipeline_run(database, run_id)
    store_cleaned_fixture(database, run["video_id"])
    analyze_cleaned_transcript(database, video_id=run["video_id"], client=Client())
    generate_brief(database, video_id=run["video_id"], briefs_path=tmp_path / "briefs")

    rendered = render_brief_page(database, tmp_path / "briefs", run_id=run_id)

    # The product name is a kicker; the video title is the document heading.
    assert '<p class="brief-kicker">ClaimLens Brief</p>' in rendered
    assert '<h1 class="brief-title">abc123XYZ_</h1>' in rendered
    assert "Report language: fr" in rendered


def test_render_brief_page_rejects_artifact_outside_briefs_dir(tmp_path):
    database = tmp_path / "claimlens.sqlite3"
    run_id = create_run(database, "https://www.youtube.com/watch?v=abc123XYZ_")
    run = db.get_pipeline_run(database, run_id)
    store_cleaned_fixture(database, run["video_id"])
    summary_id = analyze_cleaned_transcript(database, video_id=run["video_id"], client=Client())
    outside = tmp_path / "outside.md"
    outside.write_text("# Outside", encoding="utf-8")
    db.upsert_brief_artifact(
        database,
        video_id=run["video_id"],
        summary_id=summary_id,
        path=outside,
    )

    rendered = render_brief_page(database, tmp_path / "briefs", run_id=run_id)

    assert "No report is available" in rendered


def test_render_process_page_shows_step_status_failure_and_controls(tmp_path):
    database = tmp_path / "claimlens.sqlite3"
    run_id = create_run(database, "https://www.youtube.com/watch?v=abc123XYZ_")
    db.set_step_status(
        database,
        run_id=run_id,
        step="captions",
        status="failed",
        failure_message="Subtitles are unavailable.",
    )

    html = render_process_page(database, run_id=run_id)

    assert "Get captions" in html
    assert "Needs attention" in html
    assert "Subtitles are unavailable." in html
    assert "Paste a transcript fallback" in html


def test_live_process_state_is_scoped_and_has_no_numeric_progress(tmp_path):
    database = tmp_path / "claimlens.sqlite3"
    run_id = create_run(
        database,
        "https://www.youtube.com/watch?v=abc123XYZ_",
        guest_token="guest",
    )
    job_id = db.create_job(database, run_id=run_id, action="captions")
    db.update_job(database, job_id=job_id, status="running", progress=5, message="Running")

    payload = run_status_payload(
        database,
        run_id=run_id,
        user_id=None,
        guest_token="guest",
        csrf_token="csrf",
    )
    denied = run_status_payload(
        database,
        run_id=run_id,
        user_id=None,
        guest_token="other-guest",
    )

    assert payload is not None
    assert payload["active"] is True
    assert "progress" not in payload["signature"]
    assert "%" not in payload["outputs_html"]
    assert denied is None


def test_process_controls_hide_saved_profile_keys(tmp_path):
    database = tmp_path / "claimlens.sqlite3"
    db.init_db(database)
    user_id = db.create_user(database, email="user@example.test", password_hash="hash")
    db.upsert_user_api_key(
        database,
        user_id=user_id,
        provider="openai",
        encrypted_value="encrypted",
        key_fingerprint="fingerprint",
        masked_value="sk-u...cret",
    )
    run_id = create_run(
        database,
        "https://www.youtube.com/watch?v=abc123XYZ_",
        user_id=user_id,
    )
    db.set_step_status(database, run_id=run_id, step="captions", status="succeeded")
    db.set_step_status(database, run_id=run_id, step="clean_transcript", status="succeeded")

    rendered = render_process_page(
        database,
        run_id=run_id,
        user_id=user_id,
        guest_token="guest",
        context=WebContext(
            user_id=user_id,
            email="user@example.test",
            csrf_token="csrf",
            guest_token="guest",
            session_token="session",
        ),
    )

    assert 'name="openai_api_key"' not in rendered


def test_process_controls_keep_key_fields_for_guests(tmp_path):
    database = tmp_path / "claimlens.sqlite3"
    run_id = create_run(
        database,
        "https://www.youtube.com/watch?v=abc123XYZ_",
        guest_token="guest",
    )
    db.set_step_status(database, run_id=run_id, step="captions", status="succeeded")
    db.set_step_status(database, run_id=run_id, step="clean_transcript", status="succeeded")

    rendered = render_process_page(
        database,
        run_id=run_id,
        guest_token="guest",
        context=WebContext(
            user_id=None,
            email=None,
            csrf_token="csrf",
            guest_token="guest",
            session_token=None,
        ),
    )

    assert 'name="openai_api_key"' in rendered


def test_render_process_page_shows_guest_navigation(tmp_path):
    database = tmp_path / "claimlens.sqlite3"
    run_id = create_run(database, "https://www.youtube.com/watch?v=abc123XYZ_", guest_token="guest")

    rendered = render_process_page(
        database,
        run_id=run_id,
        csrf_token="csrf",
        guest_token="guest",
        context=WebContext(
            user_id=None,
            email=None,
            csrf_token="csrf",
            guest_token="guest",
            session_token=None,
        ),
    )

    assert 'href="/login"' in rendered
    assert "Paste transcript fallback" not in rendered
    assert "Active analysis" in rendered
    assert "Start another analysis" in rendered
    assert "Execution details" in rendered
    assert "Recent analyses" in rendered


def test_render_options_page_masks_saved_keys(tmp_path):
    database = tmp_path / "claimlens.sqlite3"
    db.init_db(database)
    user_id = db.create_user(
        database,
        email="user@example.test",
        password_hash=hash_password("correct horse battery"),
    )
    db.upsert_user_api_key(
        database,
        user_id=user_id,
        provider="openai",
        encrypted_value="encrypted-value",
        key_fingerprint="fingerprint",
        masked_value="sk-u...cret",
    )
    config = load_config(env={"CLAIMLENS_KEY_ENCRYPTION_SECRET": "deploy-secret"})

    rendered = render_options_page(
        database,
        config,
        context=WebContext(
            user_id=user_id,
            email="user@example.test",
            csrf_token="csrf",
            guest_token="guest",
            session_token="session",
        ),
    )

    assert "<h1>API keys</h1>" in rendered
    assert ">API keys</a>" in rendered

    assert "sk-u...cret" in rendered
    assert "encrypted-value" not in rendered


def test_render_options_page_shows_supadata_pool_without_plaintext(tmp_path):
    database = tmp_path / "claimlens.sqlite3"
    db.init_db(database)
    user_id = db.create_user(
        database,
        email="user@example.test",
        password_hash=hash_password("correct horse battery"),
    )
    save_supadata_api_key(
        database,
        user_id=user_id,
        label="free key",
        value="supadata-plain-secret",
        priority=10,
        deployment_secret="deploy-secret",
    )
    config = load_config(env={"CLAIMLENS_KEY_ENCRYPTION_SECRET": "deploy-secret"})

    rendered = render_options_page(
        database,
        config,
        context=WebContext(
            user_id=user_id,
            email="user@example.test",
            csrf_token="csrf",
            guest_token="guest",
            session_token="session",
        ),
    )

    assert "Supadata native captions" in rendered
    assert "mode=native" in rendered
    assert "supadata-plain-secret" not in rendered
    assert "mode=auto" not in rendered
    assert "mode=generate" not in rendered


def test_report_access_is_scoped_by_owner(tmp_path):
    database = tmp_path / "claimlens.sqlite3"
    db.init_db(database)
    user_id = db.create_user(
        database,
        email="user@example.test",
        password_hash=hash_password("correct horse battery"),
    )
    run_id = create_run(
        database,
        "https://www.youtube.com/watch?v=abc123XYZ_",
        user_id=user_id,
    )
    run = db.get_pipeline_run(database, run_id)
    store_cleaned_fixture(database, run["video_id"])
    summary_id = analyze_cleaned_transcript(database, video_id=run["video_id"], client=Client())
    brief = tmp_path / "briefs" / "abc123XYZ_.md"
    brief.parent.mkdir()
    brief.write_text("# Private", encoding="utf-8")
    db.upsert_brief_artifact(
        database,
        video_id=run["video_id"],
        summary_id=summary_id,
        path=brief,
    )

    denied = render_brief_page(
        database,
        tmp_path / "briefs",
        run_id=run_id,
        user_id=None,
        guest_token="guest",
    )
    allowed = render_brief_page(
        database,
        tmp_path / "briefs",
        run_id=run_id,
        user_id=user_id,
        guest_token="guest",
    )

    assert "No report is available" in denied
    assert "Private" in allowed


def completed_run(tmp_path, database, *, guest_token="guest"):
    """A run whose steps are all done, as it looks after the worker thread exits."""

    run_id = create_run(
        database,
        "https://www.youtube.com/watch?v=abc123XYZ_",
        guest_token=guest_token,
    )
    run = db.get_pipeline_run(database, run_id)
    store_cleaned_fixture(database, run["video_id"])
    analyze_cleaned_transcript(database, video_id=run["video_id"], client=Client())
    for step in ("captions", "clean_transcript", "analysis", "brief"):
        db.set_step_status(database, run_id=run_id, step=step, status="succeeded")
    generate_brief(database, video_id=run["video_id"], briefs_path=tmp_path / "briefs")
    return run_id


def test_the_step_timeline_is_visible_without_opening_anything(tmp_path):
    database = tmp_path / "claimlens.sqlite3"
    run_id = create_run(database, "https://www.youtube.com/watch?v=abc123XYZ_")
    db.set_step_status(database, run_id=run_id, step="captions", status="running")
    db.create_job(database, run_id=run_id, action="captions")

    rendered = render_process_page(database, run_id=run_id, csrf_token="csrf")

    stepper = rendered.index('id="pipeline-stepper"')
    details = rendered.index('<details class="diagnostic">')
    # The timeline is rendered before, and therefore outside, the disclosure.
    assert stepper < details
    assert rendered.count("<details class=\"diagnostic\">") == 1
    assert "Get captions" in rendered


def test_the_removed_diagnostic_views_are_no_longer_rendered(tmp_path):
    database = tmp_path / "claimlens.sqlite3"
    run_id = completed_run(tmp_path, database)

    rendered = render_process_page(
        database,
        run_id=run_id,
        guest_token="guest",
        csrf_token="csrf",
        briefs_path=tmp_path / "briefs",
    )

    assert "Background actions" not in rendered
    assert "Cleaned transcript preview" not in rendered
    assert 'class="preview"' not in rendered


def test_a_reload_settles_a_run_the_worker_finished_without_saying_so(tmp_path):
    database = tmp_path / "claimlens.sqlite3"
    run_id = completed_run(tmp_path, database)
    # The stale claim a dead worker leaves behind.
    db.set_run_status(database, run_id=run_id, status="running", current_step="brief")

    rendered = render_process_page(
        database,
        run_id=run_id,
        guest_token="guest",
        csrf_token="csrf",
        briefs_path=tmp_path / "briefs",
    )

    assert db.get_pipeline_run(database, run_id)["status"] == "succeeded"
    assert "Analysis complete" in rendered
    assert 'id="pipeline-brief"' in rendered
    # Embedded under the page heading, the brief title sits one level down.
    assert '<h2 class="brief-title">' in rendered


def test_a_reload_makes_an_abandoned_step_retryable_instead_of_stuck(tmp_path):
    database = tmp_path / "claimlens.sqlite3"
    run_id = create_run(
        database,
        "https://www.youtube.com/watch?v=abc123XYZ_",
        guest_token="guest",
    )
    db.set_step_status(database, run_id=run_id, step="captions", status="running")
    db.set_run_status(database, run_id=run_id, status="running", current_step="captions")

    run = reconcile_run_state(database, run_id)

    assert run["status"] == "failed"
    steps = {row["step"]: row["status"] for row in db.list_run_steps(database, run_id)}
    assert steps["captions"] == "failed"
    assert next_eligible_step(database, run_id) == "captions"


def test_polling_and_reloading_report_the_same_settled_state(tmp_path):
    database = tmp_path / "claimlens.sqlite3"
    run_id = completed_run(tmp_path, database)
    db.set_run_status(database, run_id=run_id, status="running", current_step="brief")

    payload = run_status_payload(
        database,
        run_id=run_id,
        user_id=None,
        guest_token="guest",
        csrf_token="csrf",
        briefs_path=tmp_path / "briefs",
    )

    assert payload is not None
    assert payload["active"] is False
    assert "Analysis complete" in payload["action_html"]
    assert payload["brief_html"] and "brief-title" in payload["brief_html"]


def test_the_top_bar_carries_the_version_and_the_archive_link(tmp_path):
    database = tmp_path / "claimlens.sqlite3"
    run_id = create_run(database, "https://www.youtube.com/watch?v=abc123XYZ_", guest_token="guest")
    context = WebContext(
        user_id=None,
        email=None,
        csrf_token="csrf",
        guest_token="guest",
        session_token=None,
    )

    rendered = render_process_page(
        database,
        run_id=run_id,
        csrf_token="csrf",
        guest_token="guest",
        context=context,
    )

    assert f'<span class="version">v{__version__}</span>' in rendered
    assert '<a href="/history"' in rendered
    # The archive is no longer a card underneath the workspace.
    assert '<div class="history-list">' not in rendered
    assert 'id="status-filter"' not in rendered


def test_the_archive_page_lists_analyses_and_keeps_the_status_filter(tmp_path):
    database = tmp_path / "claimlens.sqlite3"
    create_run(database, "https://www.youtube.com/watch?v=abc123XYZ_", guest_token="guest")

    rendered = render_history_page(database, guest_token="guest", csrf_token="csrf")

    assert "Recent analyses" in rendered
    assert 'id="status-filter"' in rendered
    assert 'href="/?run_id=' in rendered


def test_the_active_workspace_puts_the_brief_in_a_second_desktop_column(tmp_path):
    database = tmp_path / "claimlens.sqlite3"
    run_id = create_run(database, "https://www.youtube.com/watch?v=abc123XYZ_")
    db.set_step_status(database, run_id=run_id, step="captions", status="running")
    db.create_job(database, run_id=run_id, action="captions")

    rendered = render_process_page(database, run_id=run_id, csrf_token="csrf")

    assert 'class="workspace-main"' in rendered
    assert 'class="workspace-brief"' in rendered
    # One column below the breakpoint, two above it, and never a horizontal scroll.
    assert ".workspace { display:grid; grid-template-columns:minmax(0,1fr);" in rendered
    assert "@media (min-width:1080px) {" in rendered
    assert ".workspace { grid-template-columns:minmax(0,1fr) minmax(0,1.05fr); }" in rendered


def test_the_completed_workspace_gives_the_brief_the_full_width(tmp_path):
    database = tmp_path / "claimlens.sqlite3"
    run_id = completed_run(tmp_path, database)

    rendered = render_process_page(
        database,
        run_id=run_id,
        guest_token="guest",
        csrf_token="csrf",
        briefs_path=tmp_path / "briefs",
    )

    # No permanent second column competes with the brief once the run is complete.
    assert 'class="workspace-main"' not in rendered
    assert 'class="workspace-brief" id="pipeline-brief">' in rendered
    assert ".workspace.complete { grid-template-columns:minmax(0,1fr); }" in rendered
    # The completed identity, status, and Results summary are recoverable, not gone.
    assert '<div class="card recall">' in rendered
    assert "<summary" in rendered
    assert "<h2>Analysis complete</h2>" in rendered
    assert '<h2>Results</h2>' in rendered


def test_the_brief_is_rendered_as_html_and_never_as_raw_markdown(tmp_path):
    database = tmp_path / "claimlens.sqlite3"
    run_id = completed_run(tmp_path, database)

    rendered = render_process_page(
        database,
        run_id=run_id,
        guest_token="guest",
        csrf_token="csrf",
        briefs_path=tmp_path / "briefs",
    )
    brief = rendered[rendered.index('id="pipeline-brief"') :]

    assert '<article class="brief"' in brief
    assert '<h3 class="brief-section">Summary</h3>' in brief
    assert "<li>Point one</li>" in brief
    assert "## Summary" not in brief
    assert "- Point one" not in brief


def test_technical_metadata_follows_the_editorial_content_of_the_brief():
    markdown = render_markdown_brief(
        video_id="video123",
        title="A long video title",
        source_url="https://www.youtube.com/watch?v=video123",
        metadata={"Channel": "A channel"},
        summary="Summary.",
        key_points=["Point"],
        notable_claims=["Claim"],
        caveats=[],
        editorial_notes=[],
    )
    rendered = render_brief_html(markdown)

    assert rendered.index("Summary") < rendered.index("Technical details")
    assert rendered.index("Editorial Notes") < rendered.index("Technical details")
    assert rendered.index("Technical details") < rendered.index("Video ID: video123")
    # Product name and video title never read as one string.
    assert '<p class="brief-kicker">ClaimLens Brief</p>' in rendered
    assert '<h1 class="brief-title">A long video title</h1>' in rendered


def test_brief_html_links_sources_and_escapes_everything_else():
    rendered = render_brief_html(
        "- [Paper &<title>](https://example.test/paper), pubmed\n"
        "- [Local](file:///etc/passwd)\n"
        '- Cited text: "<script>alert(1)</script>"\n'
    )

    assert '<a href="https://example.test/paper"' in rendered
    assert 'rel="noopener noreferrer">Paper &amp;&lt;title&gt;</a>' in rendered
    # Only http(s) becomes a link; anything else stays inert text.
    assert '<a href="file:' not in rendered
    assert "[Local](file:///etc/passwd)" in rendered
    assert "<script>" not in rendered


def test_the_top_bar_stays_usable_on_a_phone_and_by_keyboard(tmp_path):
    database = tmp_path / "claimlens.sqlite3"
    db.init_db(database)

    rendered = render_process_page(database, csrf_token="csrf")

    # Real anchors, so tab order and activation come from the browser.
    assert '<a href="/history"' in rendered
    assert ".navlinks a:focus-visible" in rendered
    # The bar wraps instead of pushing the page sideways.
    assert "nav.app { flex-wrap:wrap; height:auto; gap:8px; padding:10px 14px; }" in rendered
    assert ".navlinks { order:3; width:100%; }" in rendered


def test_every_page_carries_the_inline_tab_icon(tmp_path):
    database = tmp_path / "claimlens.sqlite3"
    db.init_db(database)
    context = WebContext(
        user_id=None,
        email=None,
        csrf_token="csrf",
        guest_token="guest",
        session_token=None,
    )

    for rendered in (
        render_process_page(database, csrf_token="csrf"),
        render_history_page(database, csrf_token="csrf"),
        render_login_page(context=context),
    ):
        assert '<link rel="icon" type="image/svg+xml" href="data:image/svg+xml,' in rendered
        assert FAVICON_DATA_URI in rendered

    # Inlined, so the tab icon costs no request and cannot 404 behind a proxy.
    assert "%23" in FAVICON_DATA_URI  # the gradient colours survive URL encoding
    assert '"' not in FAVICON_DATA_URI


def test_the_mark_is_the_lens_play_and_review_check(tmp_path):
    database = tmp_path / "claimlens.sqlite3"
    db.init_db(database)

    rendered = render_process_page(database, csrf_token="csrf")

    # Lens, handle, check and the play triangle, drawn once in the header.
    assert '<circle cx="9.8" cy="9.8" r="8.2"/>' in rendered
    assert 'd="m11 13.6 1.6 1.6 2.8-3.4"' in rendered
    assert 'd="M7 6.2 12 9.1 7 12Z"' in rendered
    # The header mark inherits the tile colour; only the play triangle is fixed red.
    assert 'stroke="currentColor"' in LOGO_MARK
    assert LOGO_MARK.count("#e5231b") == 2
    # The tab icon and the header show the same drawing.
    assert MARK_BODY in LOGO_MARK
    assert MARK_BODY in FAVICON_SVG
