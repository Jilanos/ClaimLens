import json
from dataclasses import dataclass

from claimlens import db
from claimlens.analysis import TranscriptAnalysis, analyze_cleaned_transcript, parse_analysis_json
from claimlens.api_keys import save_supadata_api_key
from claimlens.auth import hash_password
from claimlens.briefs import generate_brief, render_markdown_brief
from claimlens.config import SourceConfig, load_config
from claimlens.pipeline import create_run, next_eligible_step
from claimlens.web import (
    HISTORY_VISIBLE_ROWS,
    WebContext,
    _run_job,
    render_brief_page,
    render_options_page,
    render_process_page,
    run_status_payload,
)


@dataclass(frozen=True)
class Client:
    model: str = "test-model"

    def analyze(self, transcript_text: str) -> TranscriptAnalysis:
        assert "clean text" in transcript_text
        return TranscriptAnalysis(
            summary="Concise summary.",
            key_points=["Point one", "Point two"],
            notable_claims=["Claim one"],
            caveats=["Caveat one"],
            editorial_notes=["Note one"],
        )


@dataclass(frozen=True)
class Segment:
    start_seconds: float
    end_seconds: float
    text: str


@dataclass(frozen=True)
class Transcript:
    video_id: str
    source: str
    language: str
    text: str
    segments: list[Segment]


def store_cleaned_fixture(database, video_id: str) -> None:
    transcript_id = db.upsert_transcript(
        database,
        Transcript(
            video_id=video_id,
            source="youtube",
            language="en",
            text="clean text",
            segments=[Segment(start_seconds=0.0, end_seconds=1.0, text="clean text")],
        ),
    )
    db.upsert_cleaned_transcript(
        database,
        video_id=video_id,
        transcript_id=transcript_id,
        text="clean text",
    )


def source_config(*, advanced: bool) -> SourceConfig:
    return SourceConfig(
        advanced_source_verification=advanced,
        enable_pubmed=True,
        enable_semantic_scholar=True,
        enable_web_search=False,
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


def test_live_script_is_present_even_without_an_active_job(tmp_path):
    database = tmp_path / "claimlens.sqlite3"
    run_id = create_run(database, "https://www.youtube.com/watch?v=abc123XYZ_")
    db.set_step_status(database, run_id=run_id, step="captions", status="succeeded")

    rendered = render_process_page(database, run_id=run_id, csrf_token="csrf")

    assert "/api/run-status?run_id=" in rendered
    assert "visibilitychange" in rendered


def test_live_payload_covers_every_dynamic_region_without_duplicating_jobs(tmp_path):
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
        "pipeline-jobs",
        "pipeline-action",
        "pipeline-controls",
        "pipeline-recovery",
        "pipeline-outputs",
    ):
        assert f'id="{region}"' in rendered
    # The jobs table is rendered once, and the results region never carries a second copy.
    assert rendered.count('id="pipeline-jobs"') == 1
    assert "Background actions" not in payload["outputs_html"]
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

    rendered = render_process_page(database, csrf_token="csrf")

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

    assert "<h1>ClaimLens Brief: abc123XYZ_</h1>" in rendered
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

    assert "captions" in html
    assert "failed" in html
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
