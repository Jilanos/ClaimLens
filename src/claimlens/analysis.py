"""OpenAI analysis boundary for cleaned transcripts."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from claimlens import db

DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_MAX_TRANSCRIPT_CHARS = 60_000
SYSTEM_PROMPT = (
    "You analyze cleaned YouTube transcripts for editorial review. "
    "Return concise JSON only with keys: summary, key_points, notable_claims, "
    "caveats, editorial_notes. notable_claims may be strings or objects with "
    "claim and transcript_excerpt. Every claim must be grounded in transcript text. "
    "Do not invent source verification."
)


class AnalysisError(RuntimeError):
    """Raised when transcript analysis cannot continue."""


@dataclass(frozen=True)
class TranscriptAnalysis:
    summary: str
    key_points: list[str]
    notable_claims: list[str]
    caveats: list[str]
    editorial_notes: list[str]
    claim_excerpts: dict[str, str] = field(default_factory=dict)


class AnalysisClient(Protocol):
    model: str

    def analyze(self, transcript_text: str) -> TranscriptAnalysis:
        """Return structured analysis for cleaned transcript text."""


class OpenAIAnalysisClient:
    """Small HTTP client so tests can mock the LLM boundary without an SDK dependency."""

    def __init__(self, *, api_key: str, model: str = DEFAULT_MODEL) -> None:
        if not api_key:
            raise AnalysisError("OPENAI_API_KEY is required for analysis.")
        self.api_key = api_key
        self.model = model

    def analyze(self, transcript_text: str) -> TranscriptAnalysis:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": transcript_text},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0,
        }
        request = Request(
            "https://api.openai.com/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=60) as response:
                body = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            raise AnalysisError(f"OpenAI analysis failed with HTTP {exc.code}.") from exc
        except (URLError, TimeoutError) as exc:
            raise AnalysisError(
                "OpenAI analysis failed because the network request timed out "
                "or could not connect."
            ) from exc
        except json.JSONDecodeError as exc:
            raise AnalysisError("OpenAI analysis response was not valid JSON.") from exc

        try:
            content = body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise AnalysisError("OpenAI analysis response was missing message content.") from exc
        return parse_analysis_json(content)


def parse_analysis_json(content: str) -> TranscriptAnalysis:
    try:
        raw = json.loads(content)
    except json.JSONDecodeError as exc:
        raise AnalysisError("OpenAI response was not valid JSON.") from exc

    claims, excerpts = _claims_and_excerpts(raw.get("notable_claims"))
    return TranscriptAnalysis(
        summary=str(raw.get("summary", "")).strip(),
        key_points=_string_list(raw.get("key_points")),
        notable_claims=claims,
        claim_excerpts=excerpts,
        caveats=_string_list(raw.get("caveats")),
        editorial_notes=_string_list(raw.get("editorial_notes")),
    )


def analyze_cleaned_transcript(
    database_path: Path | str,
    *,
    video_id: str,
    client: AnalysisClient,
    max_chars: int = DEFAULT_MAX_TRANSCRIPT_CHARS,
) -> int:
    cleaned = db.get_cleaned_transcript(database_path, video_id)
    if cleaned is None:
        raise AnalysisError("Cannot analyze before a cleaned transcript exists.")

    transcript_text = _bounded_transcript(cleaned["text"], max_chars=max_chars)
    analysis = client.analyze(transcript_text)
    if not analysis.summary:
        raise AnalysisError("Analysis response did not include a summary.")

    return db.upsert_analysis(
        database_path,
        video_id=video_id,
        model=client.model,
        summary=analysis.summary,
        key_points=analysis.key_points,
        notable_claims=analysis.notable_claims,
        claim_excerpts=_ensure_claim_excerpts(
            transcript_text,
            analysis.notable_claims,
            analysis.claim_excerpts,
        ),
        caveats=analysis.caveats,
        editorial_notes=analysis.editorial_notes,
    )


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _claims_and_excerpts(value: object) -> tuple[list[str], dict[str, str]]:
    if not isinstance(value, list):
        return [], {}
    claims: list[str] = []
    excerpts: dict[str, str] = {}
    for item in value:
        if isinstance(item, dict):
            claim = str(item.get("claim", "")).strip()
            excerpt = str(item.get("transcript_excerpt", "")).strip()
        else:
            claim = str(item).strip()
            excerpt = ""
        if not claim:
            continue
        claims.append(claim)
        if excerpt:
            excerpts[claim] = excerpt
    return claims, excerpts


def _bounded_transcript(text: str, *, max_chars: int) -> str:
    if max_chars < 1000:
        raise AnalysisError("analysis_max_chars must be at least 1000.")
    if len(text) <= max_chars:
        return text
    head = max_chars // 2
    tail = max_chars - head
    return (
        text[:head].rstrip()
        + "\n\n[ClaimLens omitted middle transcript content to stay within analysis bounds.]\n\n"
        + text[-tail:].lstrip()
    )


def _ensure_claim_excerpts(
    transcript_text: str,
    claims: list[str],
    excerpts: dict[str, str],
) -> dict[str, str]:
    grounded: dict[str, str] = {}
    lower_transcript = transcript_text.lower()
    for claim in claims:
        excerpt = excerpts.get(claim, "").strip()
        if excerpt and excerpt.lower() in lower_transcript:
            grounded[claim] = excerpt
            continue
        grounded[claim] = _nearby_excerpt(transcript_text, claim)
    return grounded


def _nearby_excerpt(transcript_text: str, claim: str, *, limit: int = 240) -> str:
    claim_terms = [term for term in claim.lower().split() if len(term) > 3]
    lower = transcript_text.lower()
    positions = [lower.find(term) for term in claim_terms if lower.find(term) >= 0]
    if not positions:
        return transcript_text[:limit].strip()
    center = min(positions)
    start = max(0, center - limit // 3)
    return transcript_text[start : start + limit].strip()
