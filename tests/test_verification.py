import itertools
import json
from dataclasses import dataclass

import pytest

from claimlens import db
from claimlens.analysis import TranscriptAnalysis, analyze_cleaned_transcript
from claimlens.briefs import generate_verified_brief
from claimlens.evidence import (
    EvidenceGrade,
    EvidenceGradingError,
    EvidenceSynthesisError,
    SynthesisSource,
    build_synthesis_prompt,
    parse_synthesis_json,
)
from claimlens.pipeline import create_run
from claimlens.verification import (
    ADAPTER_MIN_INTERVAL_SECONDS,
    COOLDOWN_MAX_WAIT_SECONDS,
    SEARCH_RETRY_ATTEMPTS,
    SOURCE_COOLDOWNS,
    SOURCE_LAST_REQUEST,
    SemanticScholarAdapter,
    SourceCandidate,
    SourceQuery,
    SourceRateLimitError,
    _search_all,
    _throttle,
    assess_claim_evidence,
    build_claim_query,
    default_adapters,
    grade_candidates,
    verify_sources,
)
from claimlens.web import render_brief_html, render_process_page


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


class UngradedAdapter:
    """Retrieval as the real adapters do it: abstracts, and no polarity opinion."""

    name = "ungraded_adapter"

    def search(self, query: SourceQuery) -> list[SourceCandidate]:
        return [
            SourceCandidate(
                title="Trial of vitamin D",
                url="https://example.test/trial",
                publisher="Journal",
                published_at="2024",
                abstract_or_snippet="Supplementation improved bone mineral density.",
                adapter=self.name,
                external_id="trial",
                metadata={"evidence_text_source": "abstract"},
            ),
            SourceCandidate(
                title="Null result",
                url="https://example.test/null",
                publisher="Journal",
                published_at="2023",
                abstract_or_snippet="No difference in bone density was observed.",
                adapter=self.name,
                external_id="null",
                metadata={"evidence_text_source": "abstract"},
            ),
            SourceCandidate(
                title="Background review",
                url="https://example.test/background",
                publisher="Journal",
                published_at="2020",
                abstract_or_snippet="An overview of bone metabolism.",
                adapter=self.name,
                external_id="background",
                metadata={"evidence_text_source": "abstract"},
            ),
        ]


class StubGrader:
    model = "stub-grader"

    def __init__(self, grades=None, error=None):
        self.error = error
        self.grades = grades or [
            EvidenceGrade("supports", "Reports improved density.", 0.9),
            EvidenceGrade("contradicts", "Reports no difference.", 0.7),
            EvidenceGrade("context", "Only background.", 0.2),
        ]
        self.calls = []

    def grade(self, *, claim, candidates):
        if self.error:
            raise self.error
        self.calls.append((claim, [c.title for c in candidates]))
        return self.grades[: len(candidates)]


def test_without_a_grader_retrieved_sources_never_become_evidence(tmp_path):
    """The regression that shipped: retrieval alone can never produce a verdict."""

    database, _ = prepared_database(tmp_path)

    verification_run_id = verify_sources(
        database,
        video_id="abc123XYZ_",
        adapters=[UngradedAdapter()],
        max_results=3,
        timeout_seconds=1,
    )

    summary = db.latest_analysis(database, "abc123XYZ_")
    claims = db.verified_claims_for_summary(database, summary["id"])
    evidence = db.evidence_for_verification(database, verification_run_id)
    assert claims[0]["verdict"] == "unclear"
    assert evidence == []
    # Retrieval still happened; only the judgement is missing.
    assert len(db.sources_for_claim(database, claims[0]["id"])) == 3


def test_grader_turns_retrieved_abstracts_into_evidence(tmp_path):
    database, _ = prepared_database(tmp_path)
    grader = StubGrader()

    verification_run_id = verify_sources(
        database,
        video_id="abc123XYZ_",
        adapters=[UngradedAdapter()],
        max_results=3,
        timeout_seconds=1,
        grader=grader,
    )

    summary = db.latest_analysis(database, "abc123XYZ_")
    claims = db.verified_claims_for_summary(database, summary["id"])
    evidence = db.evidence_for_verification(database, verification_run_id)

    assert claims[0]["verdict"] == "mixed"
    # The contextual candidate is retrieved and linked, but is not evidence.
    assert {item["polarity"] for item in evidence} == {"supports", "contradicts"}
    assert len(evidence) == 2
    assert len(db.sources_for_claim(database, claims[0]["id"])) == 3
    # The grader's reasoning reaches the database, not a generic placeholder.
    rationales = {item["rationale"] for item in evidence}
    assert "Reports improved density." in rationales
    assert claims[0]["confidence"] == pytest.approx(0.8)
    assert grader.calls[0][0] == "Vitamin D is associated with bone health"


def test_grader_supporting_only_yields_a_supported_verdict(tmp_path):
    database, _ = prepared_database(tmp_path)
    grader = StubGrader(
        grades=[
            EvidenceGrade("supports", "Affirms.", 0.6),
            EvidenceGrade("context", "Background.", None),
            EvidenceGrade("context", "Background.", None),
        ]
    )

    verify_sources(
        database,
        video_id="abc123XYZ_",
        adapters=[UngradedAdapter()],
        max_results=3,
        timeout_seconds=1,
        grader=grader,
    )

    summary = db.latest_analysis(database, "abc123XYZ_")
    claims = db.verified_claims_for_summary(database, summary["id"])
    assert claims[0]["verdict"] == "supported"
    assert claims[0]["confidence"] == pytest.approx(0.6)


def test_grading_failure_degrades_to_retrieval_without_losing_the_run(tmp_path):
    database, _ = prepared_database(tmp_path)
    grader = StubGrader(error=EvidenceGradingError("OpenAI is down"))

    verification_run_id = verify_sources(
        database,
        video_id="abc123XYZ_",
        adapters=[UngradedAdapter()],
        max_results=3,
        timeout_seconds=1,
        grader=grader,
    )

    verification = db.latest_verification_run(database, "abc123XYZ_")
    summary = db.latest_analysis(database, "abc123XYZ_")
    claims = db.verified_claims_for_summary(database, summary["id"])
    assert verification["status"] == "completed_with_warnings"
    assert "OpenAI is down" in verification["failure_message"]
    assert claims[0]["verdict"] == "unclear"
    assert db.evidence_for_verification(database, verification_run_id) == []
    # Retrieval survived the grading failure.
    assert len(db.sources_for_claim(database, claims[0]["id"])) == 3


def test_grade_candidates_records_provenance_without_mutating_inputs():
    original = SourceCandidate(
        title="Paper",
        url="https://example.test/p",
        publisher="Journal",
        published_at="2024",
        abstract_or_snippet="Findings.",
        adapter="pubmed",
        metadata={"uid": "1"},
    )

    graded = grade_candidates(
        claim="A claim",
        candidates=[original],
        grader=StubGrader(grades=[EvidenceGrade("supports", "Because.", 0.5)]),
    )

    assert graded[0].metadata["assessment_polarity"] == "supports"
    assert graded[0].metadata["assessment_rationale"] == "Because."
    assert graded[0].metadata["assessment_confidence"] == 0.5
    assert graded[0].metadata["assessment_model"] == "stub-grader"
    assert graded[0].metadata["uid"] == "1"
    # The retrieved candidate itself is untouched.
    assert original.metadata == {"uid": "1"}


def test_grade_candidates_keeps_candidates_a_short_grade_list_missed():
    candidates = UngradedAdapter().search(
        SourceQuery(claim_id=1, claim="c", video_id="v", max_results=3, timeout_seconds=1)
    )

    graded = grade_candidates(
        claim="A claim",
        candidates=candidates,
        grader=StubGrader(grades=[EvidenceGrade("supports", "Only one.", 0.5)]),
    )

    assert len(graded) == 3
    assert graded[0].metadata["assessment_polarity"] == "supports"
    assert "assessment_polarity" not in graded[2].metadata


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


def test_a_provider_with_nothing_to_say_does_not_degrade_the_run(tmp_path):
    """No candidates is an answer, not a failure: it must not label the brief an attempt."""

    database, _ = prepared_database(tmp_path)

    class Silent:
        name = "pubmed"

        def search(self, query):
            return []

    verification_run_id = verify_sources(
        database,
        video_id="abc123XYZ_",
        adapters=[Silent(), UngradedAdapter()],
        max_results=3,
        timeout_seconds=1,
        grader=StubGrader(),
    )

    verification = db.latest_verification_run(database, "abc123XYZ_")
    assert verification["status"] == "succeeded"
    assert verification["failure_message"] is None
    assert len(db.evidence_for_verification(database, verification_run_id)) == 2
    # The empty provider is still recorded, just not as a problem.
    outcomes = json.loads(verification["source_adapters_json"])
    assert {item["status"] for item in outcomes} == {"no_candidates", "candidates"}


def test_verify_sources_surfaces_no_candidates_and_rate_limits(tmp_path, monkeypatch):
    database, _run_id = prepared_database(tmp_path)
    # Exercise the retry path without paying its real backoff.
    monkeypatch.setattr("claimlens.verification.time.sleep", lambda _seconds: None)
    SOURCE_COOLDOWNS.clear()
    SOURCE_LAST_REQUEST.clear()

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


def rate_limit_query():
    return SourceQuery(
        claim_id=1,
        claim="Training strength gains",
        video_id="video123",
        max_results=5,
        timeout_seconds=1,
    )


def freeze_clock(monkeypatch, *, step=0.5):
    """Fake time so throttling and cooldowns are deterministic and instant."""

    ticks = itertools.count(100.0, step)
    monkeypatch.setattr("claimlens.verification.time.monotonic", lambda: next(ticks))
    monkeypatch.setattr("claimlens.verification.time.sleep", lambda _seconds: None)
    SOURCE_COOLDOWNS.clear()
    SOURCE_LAST_REQUEST.clear()


def test_rate_limit_cooldown_is_shared_by_adapter(monkeypatch):
    freeze_clock(monkeypatch)
    monkeypatch.setattr("claimlens.verification.SEARCH_RETRY_ATTEMPTS", 1)

    class RateLimited:
        name = "semantic_scholar"
        calls = 0

        def search(self, query):
            self.calls += 1
            raise SourceRateLimitError("limited", retry_after_seconds=30)

    adapter = RateLimited()
    first = _search_all([adapter], rate_limit_query())
    second = _search_all([adapter], rate_limit_query())

    assert adapter.calls == 1
    assert first.outcomes[0]["status"] == "rate_limited"
    assert second.outcomes[0]["status"] == "rate_limited"
    SOURCE_COOLDOWNS.clear()


def test_a_rate_limited_provider_is_retried_before_being_given_up_on(monkeypatch):
    """Semantic Scholar 429s on back-to-back calls, so one refusal must not end it."""

    freeze_clock(monkeypatch)

    class FlakyThenFine:
        name = "semantic_scholar"
        calls = 0

        def search(self, query):
            self.calls += 1
            if self.calls < 3:
                raise SourceRateLimitError("limited", retry_after_seconds=1)
            return [
                SourceCandidate(
                    title="Recovered",
                    url="https://example.test/recovered",
                    publisher="Journal",
                    published_at="2024",
                    abstract_or_snippet="Findings.",
                    adapter=self.name,
                )
            ]

    adapter = FlakyThenFine()
    result = _search_all([adapter], rate_limit_query())

    # Recovers on the third attempt, so the fourth is never needed.
    assert adapter.calls == 3
    assert result.outcomes[0]["status"] == "candidates"
    assert [c.title for c in result.candidates] == ["Recovered"]
    assert result.errors == []
    SOURCE_COOLDOWNS.clear()


def test_retries_are_bounded_and_then_the_cooldown_trips(monkeypatch):
    freeze_clock(monkeypatch)

    class AlwaysLimited:
        name = "semantic_scholar"
        calls = 0

        def search(self, query):
            self.calls += 1
            raise SourceRateLimitError("limited", retry_after_seconds=2)

    adapter = AlwaysLimited()
    result = _search_all([adapter], rate_limit_query())

    assert adapter.calls == 4
    assert result.outcomes[0]["status"] == "rate_limited"
    assert SOURCE_COOLDOWNS["semantic_scholar"] > 0
    SOURCE_COOLDOWNS.clear()


def test_throttle_spaces_out_calls_to_the_same_provider(monkeypatch):
    slept: list[float] = []
    now = [100.0]
    monkeypatch.setattr("claimlens.verification.time.monotonic", lambda: now[0])
    monkeypatch.setattr("claimlens.verification.time.sleep", lambda seconds: slept.append(seconds))
    SOURCE_LAST_REQUEST.clear()

    _throttle("semantic_scholar")
    _throttle("semantic_scholar")
    _throttle("ungraded_adapter")

    # First call is free, the second waits out the provider interval, unknown ones never wait.
    assert slept == [pytest.approx(ADAPTER_MIN_INTERVAL_SECONDS["semantic_scholar"])]
    SOURCE_LAST_REQUEST.clear()


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


def test_verified_brief_shows_why_each_source_counts(tmp_path):
    database, _ = prepared_database(tmp_path)
    verify_sources(
        database,
        video_id="abc123XYZ_",
        adapters=[UngradedAdapter()],
        max_results=3,
        timeout_seconds=1,
        grader=StubGrader(),
    )

    markdown = generate_verified_brief(
        database,
        video_id="abc123XYZ_",
        briefs_path=tmp_path / "briefs",
    ).read_text(encoding="utf-8")

    assert "Verdict: mixed (mean grading confidence 0.80)" in markdown
    assert "- Why: Reports improved density." in markdown
    assert "- Why: Reports no difference." in markdown
    assert '- Cited text: "Supplementation improved bone mineral density."' in markdown
    assert "[Trial of vitamin D](https://example.test/trial)" in markdown
    # The contextual source is not presented as evidence either way.
    assert "Only background." not in markdown


def test_semantic_scholar_falls_back_to_tldr_when_the_abstract_is_withheld(monkeypatch):
    payload = {
        "data": [
            {
                "title": "Withheld abstract paper",
                "url": "https://example.test/withheld",
                "abstract": None,
                "tldr": {"model": "tldr@v2", "text": "Isometrics increased tendon stiffness."},
                "venue": "Journal",
                "year": 2022,
                "citationCount": 41,
                "publicationTypes": ["JournalArticle"],
                "isOpenAccess": True,
                "externalIds": {"DOI": "10.1/x"},
            },
            {
                "title": "Bare record",
                "url": "https://example.test/bare",
                "abstract": None,
                "tldr": None,
                "externalIds": {},
            },
        ]
    }
    monkeypatch.setattr(
        "claimlens.verification._read_json",
        lambda url, timeout, headers=None: payload,
    )

    candidates = SemanticScholarAdapter(api_key="s2key").search(
        SourceQuery(claim_id=1, claim="Isometrics build tendons", video_id="v",
                    max_results=5, timeout_seconds=5)
    )

    assert candidates[0].abstract_or_snippet == "Isometrics increased tendon stiffness."
    assert candidates[0].metadata["evidence_text_source"] == "tldr"
    assert candidates[0].metadata["citation_count"] == 41
    assert candidates[0].metadata["is_open_access"] is True
    # No abstract and no tldr means the grader is told it is looking at a title only.
    assert candidates[1].abstract_or_snippet == "Bare record"
    assert candidates[1].metadata["evidence_text_source"] == "title_fallback"


def test_semantic_scholar_prefers_a_real_abstract_over_tldr(monkeypatch):
    payload = {
        "data": [
            {
                "title": "Full paper",
                "url": "https://example.test/full",
                "abstract": "  Randomised trial showing   a clear effect.  ",
                "tldr": {"text": "Short summary."},
                "externalIds": {},
            }
        ]
    }
    monkeypatch.setattr(
        "claimlens.verification._read_json",
        lambda url, timeout, headers=None: payload,
    )

    candidate = SemanticScholarAdapter().search(
        SourceQuery(claim_id=1, claim="c", video_id="v", max_results=5, timeout_seconds=5)
    )[0]

    assert candidate.abstract_or_snippet == "Randomised trial showing a clear effect."
    assert candidate.metadata["evidence_text_source"] == "abstract"


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


def instant_clock(monkeypatch):
    """A clock that only moves when the code under test decides to wait.

    Retry and cooldown behaviour is then observable through the recorded waits, with no
    real delay in the suite.
    """

    now = [1000.0]
    slept: list[float] = []

    def fake_sleep(seconds: float) -> None:
        slept.append(seconds)
        now[0] += seconds

    monkeypatch.setattr("claimlens.verification.time.monotonic", lambda: now[0])
    monkeypatch.setattr("claimlens.verification._sleep", fake_sleep)
    SOURCE_COOLDOWNS.clear()
    SOURCE_LAST_REQUEST.clear()
    return now, slept


def test_an_explicit_cooldown_delays_the_next_request_instead_of_skipping_it(monkeypatch):
    now, slept = instant_clock(monkeypatch)
    SOURCE_COOLDOWNS["semantic_scholar"] = now[0] + 5

    class Waited:
        name = "semantic_scholar"
        called_at: float | None = None

        def search(self, query):
            self.called_at = now[0]
            return [
                SourceCandidate(
                    title="After the cooldown",
                    url="https://example.test/after",
                    publisher="Journal",
                    published_at="2024",
                    abstract_or_snippet="Findings.",
                    adapter=self.name,
                )
            ]

    adapter = Waited()
    result = _search_all([adapter], rate_limit_query())

    assert slept == [5.0]
    assert adapter.called_at == 1005.0
    assert result.outcomes[0]["status"] == "candidates"
    assert result.limits == []
    SOURCE_COOLDOWNS.clear()


def test_a_cooldown_longer_than_the_wait_budget_is_reported_as_a_durable_limit(monkeypatch):
    now, slept = instant_clock(monkeypatch)
    SOURCE_COOLDOWNS["semantic_scholar"] = now[0] + COOLDOWN_MAX_WAIT_SECONDS + 30

    class NeverCalled:
        name = "semantic_scholar"
        calls = 0

        def search(self, query):
            self.calls += 1
            return []

    adapter = NeverCalled()
    result = _search_all([adapter], rate_limit_query())

    assert adapter.calls == 0
    assert slept == []
    assert result.outcomes[0]["status"] == "rate_limited"
    assert result.errors == []
    assert "was not checked" in result.limits[0]
    SOURCE_COOLDOWNS.clear()


def test_retry_after_is_honoured_within_a_bounded_number_of_replays(monkeypatch):
    _now, slept = instant_clock(monkeypatch)

    class LimitedTwice:
        name = "semantic_scholar"
        calls = 0

        def search(self, query):
            self.calls += 1
            if self.calls <= 2:
                raise SourceRateLimitError("limited", retry_after_seconds=2)
            return [
                SourceCandidate(
                    title="Recovered",
                    url="https://example.test/recovered",
                    publisher="Journal",
                    published_at="2024",
                    abstract_or_snippet="Findings.",
                    adapter=self.name,
                )
            ]

    adapter = LimitedTwice()
    result = _search_all([adapter], rate_limit_query())

    assert adapter.calls == 3
    # Each replay waited exactly the provider's own retry-after, and never longer.
    assert slept == [2.0, 2.0]
    assert result.outcomes[0]["attempts"] == 3
    assert result.outcomes[0]["recovered_from_rate_limit"] is True
    SOURCE_COOLDOWNS.clear()


def test_a_recovered_rate_limit_leaves_no_provider_error_in_the_report(tmp_path, monkeypatch):
    database, _run_id = prepared_database(tmp_path)
    instant_clock(monkeypatch)

    class LimitedOnce:
        name = "semantic_scholar"
        calls = 0

        def search(self, query):
            self.calls += 1
            if self.calls == 1:
                raise SourceRateLimitError("limited", retry_after_seconds=1)
            return [
                SourceCandidate(
                    title="Supportive paper",
                    url="https://example.test/support",
                    publisher="Journal",
                    published_at="2024",
                    abstract_or_snippet="Vitamin D is associated with improved bone health.",
                    adapter=self.name,
                    metadata={"assessment_polarity": "supports"},
                )
            ]

    verify_sources(
        database,
        video_id="abc123XYZ_",
        adapters=[LimitedOnce()],
        max_results=2,
        timeout_seconds=1,
    )

    verification = db.latest_verification_run(database, "abc123XYZ_")
    assert verification["status"] == "succeeded"
    assert verification["failure_message"] is None
    analysis = db.latest_analysis(database, "abc123XYZ_")
    rationales = [
        row["rationale"] for row in db.verified_claims_for_summary(database, analysis["id"])
    ]
    assert all("Adapter errors" not in text for text in rationales)
    assert all("Provider limits" not in text for text in rationales)
    SOURCE_COOLDOWNS.clear()


def test_exhausted_retries_explain_the_limit_without_claiming_full_coverage(tmp_path, monkeypatch):
    database, _run_id = prepared_database(tmp_path)
    instant_clock(monkeypatch)

    class AlwaysLimited:
        name = "semantic_scholar"
        calls = 0

        def search(self, query):
            self.calls += 1
            raise SourceRateLimitError("limited", retry_after_seconds=1)

    adapter = AlwaysLimited()
    verify_sources(
        database,
        video_id="abc123XYZ_",
        adapters=[adapter],
        max_results=2,
        timeout_seconds=1,
    )

    assert adapter.calls == SEARCH_RETRY_ATTEMPTS
    verification = db.latest_verification_run(database, "abc123XYZ_")
    assert verification["status"] == "completed_with_warnings"
    analysis = db.latest_analysis(database, "abc123XYZ_")
    rationale = db.verified_claims_for_summary(database, analysis["id"])[0]["rationale"]
    assert "not fully checked" in rationale
    assert "Coverage for this claim is therefore incomplete." in rationale
    outcomes = json.loads(verification["source_adapters_json"])
    assert outcomes[0]["attempts"] == SEARCH_RETRY_ATTEMPTS
    SOURCE_COOLDOWNS.clear()


class PolarityAdapter:
    """Retrieval whose graded polarity is fixed by the test, one candidate per entry."""

    name = "test_adapter"

    def __init__(self, polarities):
        self.polarities = polarities

    def search(self, query):
        return [
            SourceCandidate(
                title=f"Paper {index}",
                url=f"https://example.test/paper-{index}",
                publisher="Journal",
                published_at="2024",
                abstract_or_snippet=f"Finding {index} about a nearby question.",
                adapter=self.name,
                external_id=f"paper-{index}",
                metadata={"assessment_polarity": polarity},
            )
            for index, polarity in enumerate(self.polarities, start=1)
        ]


class StubSynthesizer:
    model = "stub-synthesizer"

    def __init__(self, error=None):
        self.error = error
        self.calls = []

    def synthesize(self, *, claim, verdict, sources):
        if self.error:
            raise self.error
        self.calls.append((claim, verdict, [source.polarity for source in sources]))
        return (
            "The retrieved records study a related question rather than this claim "
            "directly, and they point the same way on that narrower point."
        )


def verified_markdown(tmp_path, database, *, polarities, synthesizer=None):
    verify_sources(
        database,
        video_id="abc123XYZ_",
        adapters=[PolarityAdapter(polarities)],
        max_results=5,
        timeout_seconds=1,
        synthesizer=synthesizer,
    )
    return generate_verified_brief(
        database,
        video_id="abc123XYZ_",
        briefs_path=tmp_path / "briefs",
    ).read_text(encoding="utf-8")


@pytest.mark.parametrize(
    ("polarities", "expected"),
    [
        (["supports", "supports"], "2 supporting · 0 contradicting · Verdict: supported"),
        (["contradicts"], "0 supporting · 1 contradicting · Verdict: contradicted"),
        (["supports", "contradicts"], "1 supporting · 1 contradicting · Verdict: mixed"),
        (["context", "context"], "0 supporting · 0 contradicting · Verdict: unclear"),
    ],
)
def test_every_claim_leads_with_a_compact_signal_line(tmp_path, polarities, expected):
    database, _run_id = prepared_database(tmp_path)

    markdown = verified_markdown(tmp_path, database, polarities=polarities)

    assert f"- Signals: {expected}" in markdown


def test_an_unclear_claim_still_explains_what_the_nearby_research_shows(tmp_path):
    """The failure this fixes: 'unclear' told the reader nothing about the literature."""

    database, _run_id = prepared_database(tmp_path)
    synthesizer = StubSynthesizer()

    markdown = verified_markdown(
        tmp_path,
        database,
        polarities=["context", "context"],
        synthesizer=synthesizer,
    )

    assert "Verdict: unclear" in markdown
    assert "What the research says:" in markdown
    assert "study a related question rather than this claim directly" in markdown
    # The synthesizer saw the retrieved records and the verdict it has to explain.
    assert synthesizer.calls[0][1] == "unclear"
    assert synthesizer.calls[0][2] == ["context", "context"]
    # Caution is preserved next to the synthesis.
    assert "Human Review Disclaimer" in markdown


def test_a_claim_without_a_synthesis_says_so_instead_of_implying_one(tmp_path):
    database, _run_id = prepared_database(tmp_path)
    synthesizer = StubSynthesizer(error=EvidenceSynthesisError("no paragraph"))

    markdown = verified_markdown(
        tmp_path,
        database,
        polarities=["supports"],
        synthesizer=synthesizer,
    )

    assert "No written synthesis was produced for this claim" in markdown
    # A missing paragraph is a gap in the report, not a failed verification run.
    assert db.latest_verification_run(database, "abc123XYZ_")["status"] == "succeeded"


def test_the_synthesis_is_stored_with_the_claim_it_explains(tmp_path):
    database, _run_id = prepared_database(tmp_path)
    verify_sources(
        database,
        video_id="abc123XYZ_",
        adapters=[PolarityAdapter(["supports"])],
        max_results=5,
        timeout_seconds=1,
        synthesizer=StubSynthesizer(),
    )

    analysis = db.latest_analysis(database, "abc123XYZ_")
    claim = db.verified_claims_for_summary(database, analysis["id"])[0]
    assert "related question" in claim["evidence_synthesis"]


def test_the_synthesis_prompt_only_offers_the_records_that_were_retrieved():
    prompt = build_synthesis_prompt(
        "Vitamin D improves bone health",
        "unclear",
        [
            SynthesisSource(
                title="Trial of vitamin D",
                evidence_text="Supplementation improved bone mineral density.",
                polarity="context",
                publisher="Journal",
                published_at="2024",
                adapter="pubmed",
            ),
            SynthesisSource(
                title="Title only record",
                evidence_text="Title only record",
                evidence_text_source="title_fallback",
            ),
        ],
    )

    assert "Review verdict so far: unclear" in prompt
    assert "graded context" in prompt
    assert "No abstract available; only the title is shown." in prompt
    assert "how directly these records bear on it" in prompt


def test_synthesis_parsing_rejects_an_empty_paragraph():
    assert parse_synthesis_json('{"synthesis": "  A  paragraph. "}') == "A paragraph."
    with pytest.raises(EvidenceSynthesisError):
        parse_synthesis_json('{"synthesis": ""}')
    with pytest.raises(EvidenceSynthesisError):
        parse_synthesis_json("not json")


def test_claim_signals_render_as_labelled_pills_without_emoji(tmp_path):
    database, _run_id = prepared_database(tmp_path)
    markdown = verified_markdown(
        tmp_path,
        database,
        polarities=["supports", "contradicts"],
        synthesizer=StubSynthesizer(),
    )

    rendered = render_brief_html(markdown)

    assert '<ul class="claim-signals">' in rendered
    assert '<li class="signal supporting">1 supporting</li>' in rendered
    assert '<li class="signal contradicting">1 contradicting</li>' in rendered
    assert '<li class="signal verdict warn">Verdict: mixed' in rendered
    # Meaning never rides on a pictogram.
    assert all(ord(char) < 128 or char in "·—’" for char in rendered)
