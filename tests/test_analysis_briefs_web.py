from dataclasses import dataclass

from claimlens import db
from claimlens.analysis import TranscriptAnalysis, analyze_cleaned_transcript, parse_analysis_json
from claimlens.briefs import generate_brief, render_markdown_brief
from claimlens.pipeline import create_run
from claimlens.web import render_brief_page, render_process_page


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
