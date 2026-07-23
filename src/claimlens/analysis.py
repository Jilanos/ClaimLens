"""OpenAI analysis boundary for cleaned transcripts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from claimlens import db

DEFAULT_MODEL = "gpt-4o-mini"
SYSTEM_PROMPT = (
    "You analyze cleaned YouTube transcripts for editorial review. "
    "Return concise JSON only with keys: summary, key_points, notable_claims, "
    "caveats, editorial_notes. Do not invent source verification."
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

        content = body["choices"][0]["message"]["content"]
        return parse_analysis_json(content)


def parse_analysis_json(content: str) -> TranscriptAnalysis:
    try:
        raw = json.loads(content)
    except json.JSONDecodeError as exc:
        raise AnalysisError("OpenAI response was not valid JSON.") from exc

    return TranscriptAnalysis(
        summary=str(raw.get("summary", "")).strip(),
        key_points=_string_list(raw.get("key_points")),
        notable_claims=_string_list(raw.get("notable_claims")),
        caveats=_string_list(raw.get("caveats")),
        editorial_notes=_string_list(raw.get("editorial_notes")),
    )


def analyze_cleaned_transcript(
    database_path: Path | str,
    *,
    video_id: str,
    client: AnalysisClient,
) -> int:
    cleaned = db.get_cleaned_transcript(database_path, video_id)
    if cleaned is None:
        raise AnalysisError("Cannot analyze before a cleaned transcript exists.")

    analysis = client.analyze(cleaned["text"])
    if not analysis.summary:
        raise AnalysisError("Analysis response did not include a summary.")

    return db.upsert_analysis(
        database_path,
        video_id=video_id,
        model=client.model,
        summary=analysis.summary,
        key_points=analysis.key_points,
        notable_claims=analysis.notable_claims,
        caveats=analysis.caveats,
        editorial_notes=analysis.editorial_notes,
    )


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]
