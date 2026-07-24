import json
from dataclasses import dataclass

from claimlens import db
from claimlens.analysis import TranscriptAnalysis, analyze_cleaned_transcript
from claimlens.briefs import generate_verified_brief
from claimlens.pipeline import create_run
from claimlens.verification import (
    SOURCE_COOLDOWNS,
    SourceCandidate,
    SourceQuery,
    SourceRateLimitError,
    _search_all,
    assess_claim_evidence,
    build_claim_query,
    default_adapters,
    verify_sources,
)
from claimlens.web import render_process_page


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


@dataclass(frozen=True)
class AnalysisClient:
    model: str = "test-model"

    def analyze(self, transcript_text: str) -> TranscriptAnalysis:
        return TranscriptAnalysis(
            summary="Summary.",
            key_points=["Point"],
            notable_claims=["Vitamin D is associated with bone health"],
            caveats=["Caveat"],
            editorial_notes=["Review sources"],
        )


class Adapter:
    name = "test_adapter"

    def search(self, query: SourceQuery) -> list[SourceCandidate]:
        assert query.claim_id > 0
        assert query.video_id == "abc123XYZ_"
        return [
            SourceCandidate(
                title="Supportive paper",
                url="https://example.test/support",
                publisher="Journal",
                published_at="2024",
                abstract_or_snippet="Vitamin D is associated with improved bone health.",
                adapter=self.name,
                external_id="support",
                metadata={"assessment_polarity": "supports"},
            ),
            SourceCandidate(
                title="Contradicting paper",
                url="https://example.test/against",
                publisher="Journal",
                published_at="2023",
                abstract_or_snippet="There is no evidence that vitamin D improves bone health.",
                adapter=self.name,
                external_id="against",
                metadata={"assessment_polarity": "contradicts"},
            ),
        ]


def prepared_database(tmp_path):
    database = tmp_path / "claimlens.sqlite3"
    run_id = create_run(database, "https://www.youtube.com/watch?v=abc123XYZ_")
    transcript_id = db.upsert_transcript(
        database,
        Transcript(
            video_id="abc123XYZ_",
            source="youtube",
            language="en",
            text="clean text",
            segments=[Segment(start_seconds=0.0, end_seconds=1.0, text="clean text")],
        ),
    )
    db.upsert_cleaned_transcript(
        database,
        video_id="abc123XYZ_",
        transcript_id=transcript_id,
        text="clean text",
    )
    analyze_cleaned_transcript(database, video_id="abc123XYZ_", client=AnalysisClient())
    db.set_step_status(database, run_id=run_id, step="analysis", status="succeeded")
    return database, run_id


def test_build_claim_query_is_deterministic():
    assert build_claim_query("Vitamin D is associated with bone health!") == (
        "vitamin associated bone health"
    )


def test_assess_claim_evidence_returns_mixed_with_supporting_and_contradicting_snippets():
    assessment = assess_claim_evidence(
        claim="Vitamin D improves bone health",
        candidates=[
            SourceCandidate(
                title="Support",
                url="https://example.test/a",
                publisher="Journal",
                published_at="2024",
                abstract_or_snippet="Vitamin D is associated with improved bone health.",
                adapter="test",
                metadata={"assessment_polarity": "supports"},
            ),
            SourceCandidate(
                title="Against",
                url="https://example.test/b",
                publisher="Journal",
                published_at="2024",
                abstract_or_snippet="No evidence shows vitamin D improves bone health.",
                adapter="test",
                metadata={"assessment_polarity": "contradicts"},
            ),
        ],
    )

    assert assessment.verdict == "mixed"
    assert {item.polarity for item in assessment.evidence} == {"supports", "contradicts"}
    assert "human expert judgment" in assessment.rationale


def test_verify_sources_persists_sources_evidence_and_verdict(tmp_path):
    database, _run_id = prepared_database(tmp_path)

    verification_run_id = verify_sources(
        database,
        video_id="abc123XYZ_",
        adapters=[Adapter()],
        max_results=2,
        timeout_seconds=1,
    )

    verification = db.latest_verification_run(database, "abc123XYZ_")
    summary = db.latest_analysis(database, "abc123XYZ_")
    claims = db.verified_claims_for_summary(database, summary["id"])
    evidence = db.evidence_for_verification(database, verification_run_id)
    sources = db.sources_for_claim(database, claims[0]["id"])
    assert verification["status"] == "succeeded"
    assert claims[0]["verdict"] == "mixed"
    assert len(evidence) == 2
    assert len(sources) == 2


def test_verify_sources_surfaces_no_candidates_and_rate_limits(tmp_path):
    database, _run_id = prepared_database(tmp_path)

    class NoCandidates:
        name = "pubmed"

        def search(self, query):
            return []

    class RateLimited:
        name = "semantic_scholar"

        def search(self, query):
            raise SourceRateLimitError("limited", retry_after_seconds=0)

    verify_sources(
        database,
        video_id="abc123XYZ_",
        adapters=[NoCandidates(), RateLimited()],
        max_results=5,
        timeout_seconds=1,
    )

    verification = db.latest_verification_run(database, "abc123XYZ_")
    assert verification["status"] == "completed_with_warnings"
    assert "semantic_scholar" in verification["failure_message"]
    outcomes = json.loads(verification["source_adapters_json"])
    assert {item["status"] for item in outcomes} == {"no_candidates", "rate_limited"}

    report = generate_verified_brief(
        database,
        video_id="abc123XYZ_",
        briefs_path=tmp_path / "briefs",
    )
    markdown = report.read_text(encoding="utf-8")
    assert report.name == "abc123XYZ_.verification-attempt.md"
    assert "completed with warnings" in markdown
    assert "semantic_scholar: rate_limited" in markdown
    assert "advanced-source-verified with PubMed/Semantic Scholar candidates" not in markdown


def test_rate_limit_cooldown_is_shared_by_adapter(monkeypatch):
    SOURCE_COOLDOWNS.clear()
    clock = iter([100.0, 100.0, 101.0])
    monkeypatch.setattr("claimlens.verification.time.monotonic", lambda: next(clock))

    class RateLimited:
        name = "semantic_scholar"
        calls = 0

        def search(self, query):
            self.calls += 1
            raise SourceRateLimitError("limited", retry_after_seconds=30)

    adapter = RateLimited()
    query = SourceQuery(
        claim_id=1,
        claim="Training strength gains",
        video_id="video123",
        max_results=5,
        timeout_seconds=1,
    )
    first = _search_all([adapter], query)
    second = _search_all([adapter], query)

    assert adapter.calls == 1
    assert first.outcomes[0]["status"] == "rate_limited"
    assert second.outcomes[0]["status"] == "rate_limited"
    SOURCE_COOLDOWNS.clear()


def test_default_adapters_honor_source_switches():
    assert [
        adapter.name
        for adapter in default_adapters(
            semantic_scholar_key=None,
            ncbi_key=None,
            enable_pubmed=False,
            enable_semantic_scholar=True,
        )
    ] == ["semantic_scholar"]
    assert default_adapters(
        semantic_scholar_key=None,
        ncbi_key=None,
        enable_pubmed=False,
        enable_semantic_scholar=False,
    ) == []


def test_generate_verified_brief_includes_citations_and_status(tmp_path):
    database, _run_id = prepared_database(tmp_path)
    verify_sources(
        database,
        video_id="abc123XYZ_",
        adapters=[Adapter()],
        max_results=2,
        timeout_seconds=1,
    )

    path = generate_verified_brief(database, video_id="abc123XYZ_", briefs_path=tmp_path / "briefs")
    markdown = path.read_text(encoding="utf-8")

    assert "Source verification: Advanced-source-verified" in markdown
    assert "Verdict: mixed" in markdown
    assert "[Supportive paper](https://example.test/support)" in markdown
    assert "Human Review Disclaimer" in markdown


def test_process_page_shows_source_verification_state(tmp_path):
    database, run_id = prepared_database(tmp_path)
    verify_sources(
        database,
        video_id="abc123XYZ_",
        adapters=[Adapter()],
        max_results=2,
        timeout_seconds=1,
    )

    html = render_process_page(database, run_id=run_id)

    assert "Source verification" in html
    assert "Evidence snippets" in html
    assert "Report status" in html
    assert "Not available" in html
