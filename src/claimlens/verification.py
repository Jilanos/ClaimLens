"""Optional source verification for health/science claims."""

from __future__ import annotations

import json
import logging
import re
import threading
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from claimlens import db
from claimlens.evidence import (
    ClaimSynthesizer,
    ClaimTranslationError,
    ClaimTranslator,
    EvidenceGrader,
    EvidenceGradingError,
    EvidenceSynthesisError,
    GradableCandidate,
    SynthesisSource,
)

VERDICTS = {"supported", "contradicted", "mixed", "unclear", "not_checked"}
POLARITIES = {"supports", "contradicts", "context"}
HUMAN_REVIEW_DISCLAIMER = (
    "Source verification is an editorial aid for health/science review and does not replace "
    "human expert judgment, clinical guidance, diagnosis, or medical advice."
)
DEFAULT_ADAPTERS = ("pubmed", "semantic_scholar")
LOGGER = logging.getLogger(__name__)
SOURCE_COOLDOWNS: dict[str, float] = {}

#: Minimum seconds between requests to a provider. Semantic Scholar answers 429 to
#: back-to-back calls even with an API key, so pacing is what makes it usable at all;
#: NCBI allows a few requests per second.
ADAPTER_MIN_INTERVAL_SECONDS = {"semantic_scholar": 1.3, "pubmed": 0.4}
#: Attempts per adapter and claim, including the first. Above this the cooldown trips.
#: Semantic Scholar enforces a rolling window, so retries need seconds, not milliseconds.
SEARCH_RETRY_ATTEMPTS = 4
SEARCH_RETRY_BASE_DELAY_SECONDS = 3
SEARCH_RETRY_MAX_DELAY_SECONDS = 12
#: Longest an explicit provider cooldown may be waited out before the claim gives up on
#: that provider. Waiting is the point; waiting forever would stall the whole run.
COOLDOWN_MAX_WAIT_SECONDS = 15
SOURCE_LAST_REQUEST: dict[str, float] = {}
_THROTTLE_LOCK = threading.Lock()
#: Adapter outcomes that mean we failed to consult a provider, as opposed to
#: consulting it and learning it has nothing on this claim.
DEGRADED_OUTCOMES = frozenset({"rate_limited", "error", "failed"})


class VerificationError(RuntimeError):
    """Raised when optional source verification cannot continue."""


class SourceRateLimitError(VerificationError):
    """Raised when a source adapter returns a rate-limit response."""

    def __init__(self, message: str, *, retry_after_seconds: int | None = None) -> None:
        super().__init__(message)
        self.retry_after_seconds = retry_after_seconds


@dataclass(frozen=True)
class SourceQuery:
    claim_id: int
    claim: str
    video_id: str
    max_results: int
    timeout_seconds: int
    #: The claim in English. Providers index English, so this is what they are asked,
    #: while `claim` stays the wording the reader saw in the video.
    search_text: str = ""

    @property
    def search_claim(self) -> str:
        return self.search_text or self.claim


@dataclass(frozen=True)
class SourceCandidate:
    title: str
    url: str
    publisher: str | None
    published_at: str | None
    abstract_or_snippet: str | None
    adapter: str
    external_id: str | None = None
    metadata: dict = field(default_factory=dict)


@dataclass(frozen=True)
class EvidenceSnippet:
    source_url: str
    polarity: str
    snippet: str
    rationale: str


@dataclass(frozen=True)
class ClaimAssessment:
    verdict: str
    rationale: str
    confidence: float | None
    evidence: list[EvidenceSnippet]


@dataclass(frozen=True)
class AdapterSearchResult:
    candidates: list[SourceCandidate]
    errors: list[str]
    outcomes: list[dict]
    #: Temporary provider limits we could not wait out. Reported apart from `errors`
    #: because a throttled provider is a bounded gap, not a broken adapter.
    limits: list[str] = field(default_factory=list)


@dataclass
class RetryReport:
    """What one adapter call cost in attempts and waiting, for observability."""

    attempts: int = 0
    rate_limit_hits: int = 0
    waited_seconds: float = 0.0

    def as_outcome_fields(self) -> dict:
        return {
            "attempts": self.attempts,
            "rate_limit_hits": self.rate_limit_hits,
            "waited_seconds": round(self.waited_seconds, 2),
            "recovered_from_rate_limit": self.rate_limit_hits > 0,
        }


class SourceAdapter(Protocol):
    name: str

    def search(self, query: SourceQuery) -> list[SourceCandidate]:
        """Return normalized source candidates for a claim query."""


def build_claim_query(claim: str) -> str:
    stop_words = {
        "the", "and", "that", "with", "from", "this", "have", "has", "been",
        "being", "for", "than", "more", "less", "very", "only", "you", "your",
        "they", "their", "into", "what", "when", "where", "were", "will", "does",
        "are", "can", "just", "about", "often", "most",
    }
    words = [
        word.lower()
        for word in re.findall(r"[A-Za-z][A-Za-z0-9-]{2,}", claim)
        if word.lower() not in stop_words
    ]
    return " ".join(words[:16])


class PubMedAdapter:
    name = "pubmed"

    def __init__(self, *, api_key: str | None = None) -> None:
        self.api_key = api_key

    def search(self, query: SourceQuery) -> list[SourceCandidate]:
        term = build_claim_query(query.search_claim)
        search_params = {
            "db": "pubmed",
            "term": term,
            "retmode": "json",
            "retmax": str(query.max_results),
        }
        if self.api_key:
            search_params["api_key"] = self.api_key
        search_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?{urlencode(search_params)}"
        search_body = _read_json(search_url, timeout=query.timeout_seconds)
        ids = search_body.get("esearchresult", {}).get("idlist", [])[: query.max_results]
        if not ids:
            return []

        summary_params = {
            "db": "pubmed",
            "id": ",".join(ids),
            "retmode": "json",
        }
        if self.api_key:
            summary_params["api_key"] = self.api_key
        summary_url = (
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?"
            f"{urlencode(summary_params)}"
        )
        summary_body = _read_json(summary_url, timeout=query.timeout_seconds)
        result = summary_body.get("result", {})
        abstracts = _pubmed_abstracts(ids, api_key=self.api_key, timeout=query.timeout_seconds)
        candidates: list[SourceCandidate] = []
        for pubmed_id in ids:
            item = result.get(pubmed_id, {})
            title = item.get("title") or f"PubMed article {pubmed_id}"
            abstract = abstracts.get(str(pubmed_id))
            candidates.append(
                SourceCandidate(
                    title=title,
                    url=f"https://pubmed.ncbi.nlm.nih.gov/{pubmed_id}/",
                    publisher=item.get("source") or "PubMed",
                    published_at=item.get("pubdate"),
                    abstract_or_snippet=abstract or title,
                    adapter=self.name,
                    external_id=str(pubmed_id),
                    metadata={
                        "uid": pubmed_id,
                        "evidence_text_source": "abstract" if abstract else "title_fallback",
                    },
                )
            )
        return candidates


class SemanticScholarAdapter:
    name = "semantic_scholar"

    def __init__(self, *, api_key: str | None = None) -> None:
        self.api_key = api_key

    def search(self, query: SourceQuery) -> list[SourceCandidate]:
        params = {
            "query": build_claim_query(query.search_claim),
            "limit": str(query.max_results),
            "fields": (
                "title,url,abstract,venue,year,externalIds,authors,"
                "tldr,citationCount,publicationTypes,isOpenAccess"
            ),
        }
        url = f"https://api.semanticscholar.org/graph/v1/paper/search?{urlencode(params)}"
        headers = {"x-api-key": self.api_key} if self.api_key else None
        body = _read_json(url, timeout=query.timeout_seconds, headers=headers)
        candidates: list[SourceCandidate] = []
        for paper in body.get("data", [])[: query.max_results]:
            title = paper.get("title") or "Semantic Scholar paper"
            paper_url = paper.get("url") or _semantic_scholar_fallback_url(paper)
            # Semantic Scholar withholds many abstracts; its tldr is a usable
            # second-best so the grader sees findings rather than a bare title.
            abstract = _clean_text(paper.get("abstract"))
            tldr = _clean_text((paper.get("tldr") or {}).get("text"))
            evidence_text = abstract or tldr or title
            if abstract:
                text_source = "abstract"
            elif tldr:
                text_source = "tldr"
            else:
                text_source = "title_fallback"
            candidates.append(
                SourceCandidate(
                    title=title,
                    url=paper_url,
                    publisher=paper.get("venue") or "Semantic Scholar",
                    published_at=str(paper["year"]) if paper.get("year") else None,
                    abstract_or_snippet=evidence_text,
                    adapter=self.name,
                    external_id=_external_id(paper),
                    metadata={
                        "externalIds": paper.get("externalIds", {}),
                        "evidence_text_source": text_source,
                        "citation_count": paper.get("citationCount"),
                        "publication_types": paper.get("publicationTypes") or [],
                        "is_open_access": bool(paper.get("isOpenAccess")),
                    },
                )
            )
        return candidates


def assess_claim_evidence(
    *,
    claim: str,
    candidates: list[SourceCandidate],
) -> ClaimAssessment:
    evidence: list[EvidenceSnippet] = []
    confidences: list[float] = []
    for candidate in candidates:
        snippet = candidate.abstract_or_snippet or candidate.title
        polarity = _candidate_polarity(candidate)
        if polarity == "context":
            continue
        evidence.append(
            EvidenceSnippet(
                source_url=candidate.url,
                polarity=polarity,
                snippet=_trim(snippet),
                rationale=_candidate_rationale(candidate),
            )
        )
        graded = _candidate_confidence(candidate)
        if graded is not None:
            confidences.append(graded)

    supports = sum(1 for item in evidence if item.polarity == "supports")
    contradicts = sum(1 for item in evidence if item.polarity == "contradicts")
    confidence = round(sum(confidences) / len(confidences), 3) if confidences else None
    if supports and contradicts:
        verdict = "mixed"
        rationale = (
            f"Graded evidence is split: {supports} supporting and "
            f"{contradicts} contradicting source(s)."
        )
    elif supports:
        verdict = "supported"
        rationale = f"{supports} retrieved source(s) were graded as supporting the claim."
    elif contradicts:
        verdict = "contradicted"
        rationale = f"{contradicts} retrieved source(s) were graded as contradicting the claim."
    elif candidates:
        verdict = "unclear"
        rationale = (
            "Sources were found, but none of them directly supported or contradicted the "
            "claim, so this conservative review aid leaves the verdict open."
        )
        confidence = None
    else:
        verdict = "not_checked"
        rationale = "No candidate sources were returned by the configured adapters."
        confidence = None

    return ClaimAssessment(
        verdict=verdict,
        rationale=f"{rationale} {HUMAN_REVIEW_DISCLAIMER}",
        confidence=confidence,
        evidence=evidence,
    )


def grade_candidates(
    *,
    claim: str,
    candidates: list[SourceCandidate],
    grader: EvidenceGrader,
) -> list[SourceCandidate]:
    """Return the candidates with the grader's verdict folded into their metadata.

    `assess_claim_evidence` reads polarity from metadata, so grading stays a separate,
    optional stage: without a grader every candidate remains context.
    """

    if not candidates:
        return candidates
    grades = grader.grade(
        claim=claim,
        candidates=[
            GradableCandidate(
                title=candidate.title,
                evidence_text=candidate.abstract_or_snippet or candidate.title,
                publisher=candidate.publisher,
                published_at=candidate.published_at,
                adapter=candidate.adapter,
                evidence_text_source=str(
                    candidate.metadata.get("evidence_text_source", "abstract")
                ),
            )
            for candidate in candidates
        ],
    )
    graded: list[SourceCandidate] = []
    for candidate, grade in zip(candidates, grades, strict=False):
        metadata = dict(candidate.metadata)
        metadata.update(
            {
                "assessment_polarity": grade.polarity,
                "assessment_rationale": grade.rationale,
                "assessment_confidence": grade.confidence,
                "assessment_model": getattr(grader, "model", "unknown"),
            }
        )
        graded.append(replace(candidate, metadata=metadata))
    # A short grade list must not silently drop candidates.
    graded.extend(candidates[len(graded) :])
    return graded


def verify_sources(
    database_path: Path | str,
    *,
    video_id: str,
    adapters: list[SourceAdapter],
    max_results: int = 5,
    timeout_seconds: int = 20,
    grader: EvidenceGrader | None = None,
    synthesizer: ClaimSynthesizer | None = None,
    translator: ClaimTranslator | None = None,
) -> int:
    analysis = db.latest_analysis(database_path, video_id)
    if analysis is None:
        raise VerificationError("Cannot verify sources before analysis exists.")

    claims = db.claims_for_summary(database_path, analysis["id"])
    if not claims:
        raise VerificationError("Cannot verify sources because analysis has no notable claims.")

    verification_run_id = db.create_verification_run(
        database_path,
        video_id=video_id,
        summary_id=analysis["id"],
        adapters=[adapter.name for adapter in adapters],
    )
    adapter_results: list[dict] = []
    try:
        search_texts = _english_search_texts(translator, claims, adapter_results)
        for claim in claims:
            search_text = search_texts[claim["id"]]
            query = SourceQuery(
                claim_id=claim["id"],
                claim=claim["claim"],
                video_id=video_id,
                max_results=max_results,
                timeout_seconds=timeout_seconds,
                search_text=search_text,
            )
            search_result = _search_all(adapters, query)
            adapter_results.extend(
                {"claim_id": claim["id"], **outcome} for outcome in search_result.outcomes
            )
            candidates = search_result.candidates
            grading_errors: list[str] = []
            if grader is not None and candidates:
                try:
                    # Judge in the language the abstracts are written in; the grader
                    # writes its rationale in the report language on its own.
                    candidates = grade_candidates(
                        claim=search_text,
                        candidates=candidates,
                        grader=grader,
                    )
                except EvidenceGradingError as exc:
                    # Retrieval already succeeded; degrade to ungraded rather than lose it.
                    LOGGER.warning("Evidence grading failed for claim %s: %s", claim["id"], exc)
                    grading_errors.append(f"evidence_grading: {exc}")
                    adapter_results.append(
                        {
                            "claim_id": claim["id"],
                            "adapter": "evidence_grading",
                            "status": "failed",
                            "candidate_count": 0,
                            "message": str(exc),
                        }
                    )
            source_ids_by_url: dict[str, int] = {}
            for candidate in candidates:
                source_id = db.upsert_source(
                    database_path,
                    title=candidate.title,
                    url=candidate.url,
                    publisher=candidate.publisher,
                    published_at=candidate.published_at,
                    abstract_or_snippet=candidate.abstract_or_snippet,
                    adapter=candidate.adapter,
                    external_id=candidate.external_id,
                    metadata=candidate.metadata,
                )
                source_ids_by_url[candidate.url] = source_id
                db.link_claim_source(
                    database_path,
                    claim_id=claim["id"],
                    source_id=source_id,
                    relevance="candidate",
                    notes=f"Retrieved by {candidate.adapter}",
                )

            assessment = assess_claim_evidence(claim=claim["claim"], candidates=candidates)
            rationale = assessment.rationale
            reported_errors = search_result.errors + grading_errors
            if reported_errors:
                rationale = f"{rationale} Adapter errors: {'; '.join(reported_errors)}"
            if search_result.limits:
                # A provider limit is a coverage gap, and saying so is the honest
                # alternative to implying the claim was checked everywhere.
                rationale = (
                    f"{rationale} Provider limits: {'; '.join(search_result.limits)} "
                    "Coverage for this claim is therefore incomplete."
                )
            db.update_claim_verdict(
                database_path,
                claim_id=claim["id"],
                verdict=assessment.verdict,
                rationale=rationale,
                confidence=assessment.confidence,
            )
            db.update_claim_evidence_synthesis(
                database_path,
                claim_id=claim["id"],
                synthesis=_synthesize_claim(
                    synthesizer,
                    claim=claim,
                    claim_text=search_text,
                    verdict=assessment.verdict,
                    candidates=candidates,
                    adapter_results=adapter_results,
                ),
            )
            for snippet in assessment.evidence:
                source_id = source_ids_by_url.get(snippet.source_url)
                if source_id is None:
                    continue
                db.insert_evidence_snippet(
                    database_path,
                    verification_run_id=verification_run_id,
                    claim_id=claim["id"],
                    source_id=source_id,
                    polarity=snippet.polarity,
                    snippet=snippet.snippet,
                    rationale=snippet.rationale,
                )
        has_candidates = any(item["candidate_count"] > 0 for item in adapter_results)
        # A provider legitimately having nothing on a claim is an outcome, not an
        # incident. Only a provider we failed to reach degrades the run.
        degraded = [item for item in adapter_results if item["status"] in DEGRADED_OUTCOMES]
        verification_status = (
            "succeeded" if has_candidates and not degraded else "completed_with_warnings"
        )
        warning_messages = [
            f"{item['adapter']}: {item['message']}" for item in degraded if item.get("message")
        ]
        db.finish_verification_run(
            database_path,
            verification_run_id=verification_run_id,
            status=verification_status,
            failure_message="; ".join(warning_messages) if warning_messages else None,
            adapter_results=adapter_results,
        )
    except Exception as exc:
        db.finish_verification_run(
            database_path,
            verification_run_id=verification_run_id,
            status="failed",
            failure_message=str(exc),
            adapter_results=adapter_results,
        )
        raise
    return verification_run_id


def _english_search_texts(
    translator: ClaimTranslator | None,
    claims,
    adapter_results: list[dict],
) -> dict[int, str]:
    """Map each claim id to the wording the providers will actually be asked.

    PubMed and Semantic Scholar index English, so a claim stated in another language
    finds nothing and reads as "the science is silent" when nothing was ever asked.
    """

    originals = [str(claim["claim"]) for claim in claims]
    english = originals
    if translator is not None and originals:
        try:
            english = translator.translate(claims=originals)
        except ClaimTranslationError as exc:
            LOGGER.warning("Claim translation failed; searching the claims as written: %s", exc)
            adapter_results.append(
                {
                    "adapter": "claim_translation",
                    "status": "unavailable",
                    "candidate_count": 0,
                    "message": str(exc),
                }
            )
            english = originals
    # A short list must never shift claims onto the wrong search text.
    if len(english) != len(originals):
        LOGGER.warning("Claim translation returned %d of %d claims", len(english), len(originals))
        english = list(english) + originals[len(english) :]
    return {
        claim["id"]: (text.strip() or originals[index])
        for index, (claim, text) in enumerate(zip(claims, english, strict=False))
    }


def _synthesize_claim(
    synthesizer: ClaimSynthesizer | None,
    *,
    claim,
    claim_text: str,
    verdict: str,
    candidates: list[SourceCandidate],
    adapter_results: list[dict],
) -> str | None:
    """Describe what the retrieved records say, including when the verdict stays open.

    A missing paragraph is recorded but never degrades the run: the brief already has a
    fallback that says the synthesis is absent, which is honest and cheap.
    """

    if synthesizer is None or not candidates:
        return None
    try:
        return synthesizer.synthesize(
            claim=claim_text,
            verdict=verdict,
            sources=[
                SynthesisSource(
                    title=candidate.title,
                    evidence_text=candidate.abstract_or_snippet or candidate.title,
                    polarity=_candidate_polarity(candidate),
                    publisher=candidate.publisher,
                    published_at=candidate.published_at,
                    adapter=candidate.adapter,
                    evidence_text_source=str(
                        candidate.metadata.get("evidence_text_source", "abstract")
                    ),
                )
                for candidate in candidates
            ],
        )
    except EvidenceSynthesisError as exc:
        LOGGER.warning("Claim synthesis failed for claim %s: %s", claim["id"], exc)
        adapter_results.append(
            {
                "claim_id": claim["id"],
                "adapter": "evidence_synthesis",
                "status": "unavailable",
                "candidate_count": 0,
                "message": str(exc),
            }
        )
        return None


def default_adapters(
    *,
    semantic_scholar_key: str | None,
    ncbi_key: str | None,
    enable_pubmed: bool = True,
    enable_semantic_scholar: bool = True,
) -> list[SourceAdapter]:
    adapters: list[SourceAdapter] = []
    if enable_pubmed:
        adapters.append(PubMedAdapter(api_key=ncbi_key))
    if enable_semantic_scholar:
        adapters.append(SemanticScholarAdapter(api_key=semantic_scholar_key))
    return adapters


def _search_all(adapters: list[SourceAdapter], query: SourceQuery) -> AdapterSearchResult:
    candidates: list[SourceCandidate] = []
    errors: list[str] = []
    limits: list[str] = []
    outcomes: list[dict] = []
    for adapter in adapters:
        query_text = build_claim_query(query.search_claim)
        report = RetryReport()
        unwaited = _await_cooldown(adapter.name, report)
        if unwaited > 0:
            message = (
                f"Provider cooldown of {int(unwaited) + 1}s exceeds the "
                f"{COOLDOWN_MAX_WAIT_SECONDS}s wait budget, so this claim was not checked "
                f"against {adapter.name}."
            )
            limits.append(f"{adapter.name}: {message}")
            outcomes.append(
                {
                    "adapter": adapter.name,
                    "status": "rate_limited",
                    "candidate_count": 0,
                    "message": message,
                    "query": query_text,
                    **report.as_outcome_fields(),
                }
            )
            continue
        try:
            adapter_candidates = _search_with_retry(adapter, query, report)
            candidates.extend(adapter_candidates)
            # A limit we waited out is history, not a finding: it stays in the outcome
            # for observability and never reaches the reader as an adapter error.
            outcomes.append(
                {
                    "adapter": adapter.name,
                    "status": "candidates" if adapter_candidates else "no_candidates",
                    "candidate_count": len(adapter_candidates),
                    "message": None if adapter_candidates else "No candidates returned.",
                    "query": query_text,
                    **report.as_outcome_fields(),
                }
            )
        except SourceRateLimitError as exc:
            delay = max(1, exc.retry_after_seconds or 3)
            SOURCE_COOLDOWNS[adapter.name] = max(
                SOURCE_COOLDOWNS.get(adapter.name, 0.0),
                time.monotonic() + delay,
            )
            message = (
                f"Still rate limited after {report.attempts} attempt(s) and "
                f"{report.waited_seconds:.0f}s of waiting, so this claim was not fully "
                f"checked against {adapter.name}; the provider asks for {delay}s more."
            )
            LOGGER.warning(
                "Source adapter rate limited for claim %s: %s",
                query.claim_id,
                adapter.name,
            )
            limits.append(f"{adapter.name}: {message}")
            outcomes.append(
                {
                    "adapter": adapter.name,
                    "status": "rate_limited",
                    "candidate_count": 0,
                    "message": message,
                    "query": query_text,
                    **report.as_outcome_fields(),
                }
            )
        except Exception as exc:
            message = str(exc)
            LOGGER.warning("Source adapter failed for claim %s: %s", query.claim_id, message)
            errors.append(f"{adapter.name}: {message}")
            outcomes.append(
                {
                    "adapter": adapter.name,
                    "status": "error",
                    "candidate_count": 0,
                    "message": message,
                    "query": query_text,
                    **report.as_outcome_fields(),
                }
            )
    return AdapterSearchResult(
        candidates=candidates,
        errors=errors,
        outcomes=outcomes,
        limits=limits,
    )


def _await_cooldown(adapter_name: str, report: RetryReport) -> float:
    """Wait out a known provider cooldown before emitting a request.

    Returns the cooldown seconds we refused to wait, so the caller can report a durable
    limit instead of hammering a provider that already told us to stop.
    """

    remaining = SOURCE_COOLDOWNS.get(adapter_name, 0.0) - time.monotonic()
    if remaining <= 0:
        return 0.0
    if remaining > COOLDOWN_MAX_WAIT_SECONDS:
        return remaining
    LOGGER.info("Waiting out a %.1fs cooldown before calling %s", remaining, adapter_name)
    _sleep(remaining)
    report.waited_seconds += remaining
    SOURCE_COOLDOWNS.pop(adapter_name, None)
    return 0.0


def _search_with_retry(
    adapter: SourceAdapter,
    query: SourceQuery,
    report: RetryReport | None = None,
) -> list[SourceCandidate]:
    """Pace requests to a provider and retry its 429s before giving up on the claim."""

    report = report if report is not None else RetryReport()
    attempts = max(1, SEARCH_RETRY_ATTEMPTS)
    for attempt in range(1, attempts + 1):
        report.attempts = attempt
        _throttle(adapter.name)
        try:
            return adapter.search(query)
        except SourceRateLimitError as exc:
            report.rate_limit_hits += 1
            if attempt == attempts:
                raise
            delay = min(
                max(
                    1,
                    exc.retry_after_seconds
                    or SEARCH_RETRY_BASE_DELAY_SECONDS * 2 ** (attempt - 1),
                ),
                SEARCH_RETRY_MAX_DELAY_SECONDS,
            )
            LOGGER.info(
                "Retrying %s after rate limit (attempt %s/%s, waiting %ss)",
                adapter.name,
                attempt,
                attempts,
                delay,
            )
            report.waited_seconds += delay
            _sleep(delay)
    raise SourceRateLimitError("Rate limit retries were exhausted.")


def _throttle(adapter_name: str) -> None:
    """Space out calls to one provider, across every thread that verifies concurrently."""

    interval = ADAPTER_MIN_INTERVAL_SECONDS.get(adapter_name, 0.0)
    if interval <= 0:
        return
    with _THROTTLE_LOCK:
        wait = SOURCE_LAST_REQUEST.get(adapter_name, 0.0) + interval - time.monotonic()
        if wait > 0:
            _sleep(wait)
        SOURCE_LAST_REQUEST[adapter_name] = time.monotonic()


def _sleep(seconds: float) -> None:
    """The one waiting boundary, so retry behaviour is testable without real delay."""

    if seconds > 0:
        time.sleep(seconds)


def _candidate_polarity(candidate: SourceCandidate) -> str:
    polarity = str(candidate.metadata.get("assessment_polarity", "context"))
    return polarity if polarity in POLARITIES else "context"


def _candidate_rationale(candidate: SourceCandidate) -> str:
    rationale = str(candidate.metadata.get("assessment_rationale", "")).strip()
    if rationale:
        return rationale
    return f"{candidate.adapter} candidate supplied explicit evidence polarity."


def _candidate_confidence(candidate: SourceCandidate) -> float | None:
    value = candidate.metadata.get("assessment_confidence")
    try:
        number = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if number != number:  # NaN
        return None
    return max(0.0, min(1.0, number))


def _clean_text(value: object) -> str:
    return " ".join(str(value).split()) if value else ""


def _read_json(url: str, *, timeout: int, headers: dict[str, str] | None = None) -> dict:
    request = Request(url, headers=headers or {})
    try:
        with urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        if exc.code == 429:
            retry_after = _retry_after_seconds(exc)
            raise SourceRateLimitError(
                "Source request was rate limited (HTTP 429).",
                retry_after_seconds=retry_after,
            ) from exc
        raise VerificationError(f"Source request failed with HTTP {exc.code}.") from exc
    except (URLError, TimeoutError) as exc:
        raise VerificationError(
            "Source request failed because the network request timed out or could not connect."
        ) from exc
    except json.JSONDecodeError as exc:
        raise VerificationError("Source response was not valid JSON.") from exc


def _retry_after_seconds(exc: HTTPError) -> int | None:
    value = exc.headers.get("Retry-After") if exc.headers else None
    try:
        return max(0, int(value)) if value is not None else None
    except (TypeError, ValueError):
        return None


def _pubmed_abstracts(
    ids: list[str],
    *,
    api_key: str | None,
    timeout: int,
) -> dict[str, str]:
    if not ids:
        return {}
    params = {"db": "pubmed", "id": ",".join(ids), "retmode": "xml"}
    if api_key:
        params["api_key"] = api_key
    url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?{urlencode(params)}"
    request = Request(url)
    try:
        with urlopen(request, timeout=timeout) as response:
            root = ET.fromstring(response.read())
    except Exception as exc:
        LOGGER.warning("PubMed abstract fetch failed: %s", exc)
        return {}
    abstracts: dict[str, str] = {}
    for article in root.findall(".//PubmedArticle"):
        pmid = article.findtext(".//PMID")
        parts = [
            "".join(text.itertext()).strip()
            for text in article.findall(".//AbstractText")
            if "".join(text.itertext()).strip()
        ]
        if pmid and parts:
            abstracts[pmid] = " ".join(parts)
    return abstracts


def _semantic_scholar_fallback_url(paper: dict) -> str:
    external_ids = paper.get("externalIds") or {}
    if external_ids.get("DOI"):
        return f"https://doi.org/{external_ids['DOI']}"
    paper_id = paper.get("paperId") or "unknown"
    return f"https://www.semanticscholar.org/paper/{paper_id}"


def _external_id(paper: dict) -> str | None:
    external_ids = paper.get("externalIds") or {}
    return external_ids.get("DOI") or external_ids.get("PubMed") or paper.get("paperId")


def _trim(text: str, limit: int = 500) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3].rstrip() + "..."
