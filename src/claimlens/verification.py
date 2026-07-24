"""Optional source verification for health/science claims."""

from __future__ import annotations

import json
import logging
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from claimlens import db

VERDICTS = {"supported", "contradicted", "mixed", "unclear", "not_checked"}
POLARITIES = {"supports", "contradicts", "context"}
HUMAN_REVIEW_DISCLAIMER = (
    "Source verification is an editorial aid for health/science review and does not replace "
    "human expert judgment, clinical guidance, diagnosis, or medical advice."
)
DEFAULT_ADAPTERS = ("pubmed", "semantic_scholar")
LOGGER = logging.getLogger(__name__)


class VerificationError(RuntimeError):
    """Raised when optional source verification cannot continue."""


@dataclass(frozen=True)
class SourceQuery:
    claim_id: int
    claim: str
    video_id: str
    max_results: int
    timeout_seconds: int


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


class SourceAdapter(Protocol):
    name: str

    def search(self, query: SourceQuery) -> list[SourceCandidate]:
        """Return normalized source candidates for a claim query."""


def build_claim_query(claim: str) -> str:
    words = [
        word.lower()
        for word in re.findall(r"[A-Za-z][A-Za-z0-9-]{2,}", claim)
        if word.lower() not in {"the", "and", "that", "with", "from", "this", "have", "has"}
    ]
    return " ".join(words[:12])


class PubMedAdapter:
    name = "pubmed"

    def __init__(self, *, api_key: str | None = None) -> None:
        self.api_key = api_key

    def search(self, query: SourceQuery) -> list[SourceCandidate]:
        term = build_claim_query(query.claim)
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
            "query": build_claim_query(query.claim),
            "limit": str(query.max_results),
            "fields": "title,url,abstract,venue,year,externalIds,authors",
        }
        url = f"https://api.semanticscholar.org/graph/v1/paper/search?{urlencode(params)}"
        headers = {"x-api-key": self.api_key} if self.api_key else None
        body = _read_json(url, timeout=query.timeout_seconds, headers=headers)
        candidates: list[SourceCandidate] = []
        for paper in body.get("data", [])[: query.max_results]:
            title = paper.get("title") or "Semantic Scholar paper"
            paper_url = paper.get("url") or _semantic_scholar_fallback_url(paper)
            candidates.append(
                SourceCandidate(
                    title=title,
                    url=paper_url,
                    publisher=paper.get("venue") or "Semantic Scholar",
                    published_at=str(paper["year"]) if paper.get("year") else None,
                    abstract_or_snippet=paper.get("abstract") or title,
                    adapter=self.name,
                    external_id=_external_id(paper),
                    metadata={"externalIds": paper.get("externalIds", {})},
                )
            )
        return candidates


def assess_claim_evidence(
    *,
    claim: str,
    candidates: list[SourceCandidate],
) -> ClaimAssessment:
    evidence: list[EvidenceSnippet] = []
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
                rationale=f"{candidate.adapter} candidate supplied explicit evidence polarity.",
            )
        )

    supports = sum(1 for item in evidence if item.polarity == "supports")
    contradicts = sum(1 for item in evidence if item.polarity == "contradicts")
    if supports and contradicts:
        verdict = "mixed"
        rationale = "Available snippets include both supporting and contradicting evidence."
        confidence = None
    elif supports:
        verdict = "supported"
        rationale = "Available evidence was marked as supporting by the assessment boundary."
        confidence = None
    elif contradicts:
        verdict = "contradicted"
        rationale = "Available evidence was marked as contradicting by the assessment boundary."
        confidence = None
    elif candidates:
        verdict = "unclear"
        rationale = (
            "Sources were found, but this conservative review-aid boundary did not classify "
            "them as clearly supporting or contradicting the claim."
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


def verify_sources(
    database_path: Path | str,
    *,
    video_id: str,
    adapters: list[SourceAdapter],
    max_results: int = 5,
    timeout_seconds: int = 20,
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
    try:
        for claim in claims:
            query = SourceQuery(
                claim_id=claim["id"],
                claim=claim["claim"],
                video_id=video_id,
                max_results=max_results,
                timeout_seconds=timeout_seconds,
            )
            search_result = _search_all(adapters, query)
            candidates = search_result.candidates
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
            if search_result.errors:
                rationale = (
                    f"{rationale} Adapter errors: "
                    f"{'; '.join(search_result.errors)}"
                )
            db.update_claim_verdict(
                database_path,
                claim_id=claim["id"],
                verdict=assessment.verdict,
                rationale=rationale,
                confidence=assessment.confidence,
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
        db.finish_verification_run(
            database_path,
            verification_run_id=verification_run_id,
            status="succeeded",
        )
    except Exception as exc:
        db.finish_verification_run(
            database_path,
            verification_run_id=verification_run_id,
            status="failed",
            failure_message=str(exc),
        )
        raise
    return verification_run_id


def default_adapters(
    *,
    semantic_scholar_key: str | None,
    ncbi_key: str | None,
) -> list[SourceAdapter]:
    return [
        PubMedAdapter(api_key=ncbi_key),
        SemanticScholarAdapter(api_key=semantic_scholar_key),
    ]


def _search_all(adapters: list[SourceAdapter], query: SourceQuery) -> AdapterSearchResult:
    candidates: list[SourceCandidate] = []
    errors: list[str] = []
    for adapter in adapters:
        try:
            candidates.extend(adapter.search(query))
        except Exception as exc:
            message = f"{adapter.name}: {exc}"
            LOGGER.warning("Source adapter failed for claim %s: %s", query.claim_id, message)
            errors.append(message)
            continue
    return AdapterSearchResult(candidates=candidates, errors=errors)


def _candidate_polarity(candidate: SourceCandidate) -> str:
    polarity = str(candidate.metadata.get("assessment_polarity", "context"))
    return polarity if polarity in POLARITIES else "context"


def _read_json(url: str, *, timeout: int, headers: dict[str, str] | None = None) -> dict:
    request = Request(url, headers=headers or {})
    try:
        with urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise VerificationError(f"Source request failed with HTTP {exc.code}.") from exc
    except (URLError, TimeoutError) as exc:
        raise VerificationError(
            "Source request failed because the network request timed out or could not connect."
        ) from exc
    except json.JSONDecodeError as exc:
        raise VerificationError("Source response was not valid JSON.") from exc


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
