"""LLM boundary that grades retrieved abstracts against a claim.

Retrieval finds papers; it cannot say whether a paper backs a claim. This module is
the missing half: it reads the abstract text an adapter returned and labels each
candidate as supporting, contradicting, or merely contextual.

The grader is deliberately conservative. These are health and science claims, so an
abstract that is merely on-topic is context, not support, and anything uncertain
falls back to context. A wrong "supported" verdict is far more damaging here than a
missed one.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

LOGGER = logging.getLogger(__name__)

DEFAULT_MODEL = "gpt-4o-mini"
#: Candidates graded per request. Keeps one prompt well inside context limits.
DEFAULT_BATCH_SIZE = 10
#: Abstracts are trimmed to keep a batch prompt bounded.
MAX_EVIDENCE_CHARS = 1_400
POLARITIES = ("supports", "contradicts", "context")

SYSTEM_PROMPT = (
    "You grade scientific abstracts against a single claim for an editorial "
    "review aid. For each numbered candidate, decide whether its text supports "
    "the claim, contradicts it, or is only context.\n"
    "Ask one question: does this text state a finding that would make the claim "
    "true, or make it false? If neither, it is context.\n"
    "Rules:\n"
    '- "supports" only when the candidate reports a finding that affirms the '
    "claim as stated.\n"
    '- "contradicts" only when it reports a finding that conflicts with the '
    "claim as stated.\n"
    "- Studying the same subject is NOT support. A paper about the same body "
    "part, condition, or intervention is context unless its findings settle "
    "this specific claim.\n"
    "- If the claim states a number, proportion, percentage, or ranking, it is "
    "supported only by text reporting a comparable figure. Do not treat "
    '"this is common" or "this matters" as confirming a statistic.\n'
    "- If the claim is about a general population but the text studies a narrow "
    "or unrelated group, that is context.\n"
    '- "context" also covers background, title-only records with no abstract, '
    "off-topic results, and every case where you are not confident.\n"
    "- Judge only from the text supplied. Never use outside knowledge and never "
    "invent findings.\n"
    "- When in doubt, answer context. Over-claiming support is the worst "
    "possible error here.\n"
    "Give each grade a one-sentence rationale quoting or paraphrasing the "
    "supplied text, and a confidence between 0 and 1.\n"
    'Return JSON only: {"gradings": [{"index": <int>, "polarity": '
    '"supports|contradicts|context", "rationale": "<one sentence>", '
    '"confidence": <0..1>}]}. Grade every candidate exactly once.'
)


class EvidenceGradingError(RuntimeError):
    """Raised when the grading boundary cannot return usable grades."""


@dataclass(frozen=True)
class GradableCandidate:
    """One retrieved source, reduced to what the grader is allowed to see."""

    title: str
    evidence_text: str
    publisher: str | None = None
    published_at: str | None = None
    adapter: str | None = None
    #: "abstract" when the text is a real abstract, "title_fallback" otherwise.
    evidence_text_source: str = "abstract"


@dataclass(frozen=True)
class EvidenceGrade:
    polarity: str
    rationale: str
    confidence: float | None


class EvidenceGrader(Protocol):
    model: str

    def grade(self, *, claim: str, candidates: list[GradableCandidate]) -> list[EvidenceGrade]:
        """Return one grade per candidate, in the order the candidates were given."""


class OpenAIEvidenceGrader:
    """Small HTTP client so tests can mock the LLM boundary without an SDK dependency."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str = DEFAULT_MODEL,
        batch_size: int = DEFAULT_BATCH_SIZE,
        timeout_seconds: int = 60,
    ) -> None:
        if not api_key:
            raise EvidenceGradingError("An OpenAI API key is required for evidence grading.")
        self.api_key = api_key
        self.model = model
        self.batch_size = max(1, batch_size)
        self.timeout_seconds = timeout_seconds

    def grade(self, *, claim: str, candidates: list[GradableCandidate]) -> list[EvidenceGrade]:
        grades: list[EvidenceGrade] = []
        for start in range(0, len(candidates), self.batch_size):
            batch = candidates[start : start + self.batch_size]
            grades.extend(self._grade_batch(claim=claim, candidates=batch))
        return grades

    def _grade_batch(
        self,
        *,
        claim: str,
        candidates: list[GradableCandidate],
    ) -> list[EvidenceGrade]:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_grading_prompt(claim, candidates)},
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
            with urlopen(request, timeout=self.timeout_seconds) as response:
                body = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            raise EvidenceGradingError(f"Evidence grading failed with HTTP {exc.code}.") from exc
        except (URLError, TimeoutError) as exc:
            raise EvidenceGradingError(
                "Evidence grading failed because the network request timed out "
                "or could not connect."
            ) from exc
        except json.JSONDecodeError as exc:
            raise EvidenceGradingError("Evidence grading response was not valid JSON.") from exc

        try:
            content = body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise EvidenceGradingError(
                "Evidence grading response was missing message content."
            ) from exc
        return parse_grading_json(content, expected=len(candidates))


def build_grading_prompt(claim: str, candidates: list[GradableCandidate]) -> str:
    lines = [f"Claim: {claim.strip()}", "", "Candidates:"]
    for index, candidate in enumerate(candidates, start=1):
        header = f"[{index}] {candidate.title.strip() or 'Untitled record'}"
        meta = " · ".join(
            part
            for part in (
                candidate.publisher or None,
                candidate.published_at or None,
                candidate.adapter or None,
            )
            if part
        )
        if meta:
            header += f" ({meta})"
        lines.append(header)
        if candidate.evidence_text_source != "abstract":
            lines.append("No abstract available; only the title is shown.")
        lines.append(_trim(candidate.evidence_text or candidate.title))
        lines.append("")
    lines.append(f"Grade all {len(candidates)} candidates.")
    return "\n".join(lines)


def parse_grading_json(content: str, *, expected: int) -> list[EvidenceGrade]:
    """Turn a grading response into exactly `expected` grades, defaulting to context."""

    try:
        raw = json.loads(content)
    except json.JSONDecodeError as exc:
        raise EvidenceGradingError("Evidence grading response was not valid JSON.") from exc

    entries = raw.get("gradings") if isinstance(raw, dict) else None
    if not isinstance(entries, list):
        raise EvidenceGradingError("Evidence grading response had no gradings array.")

    by_index: dict[int, EvidenceGrade] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        try:
            index = int(entry.get("index"))
        except (TypeError, ValueError):
            continue
        if not 1 <= index <= expected or index in by_index:
            continue
        by_index[index] = EvidenceGrade(
            polarity=_polarity(entry.get("polarity")),
            rationale=str(entry.get("rationale", "")).strip()
            or "The grader returned no rationale.",
            confidence=_confidence(entry.get("confidence")),
        )

    missing = [index for index in range(1, expected + 1) if index not in by_index]
    if missing:
        LOGGER.info("Evidence grading omitted %d candidate(s); defaulting to context", len(missing))
    # A missing grade must never become evidence, so it falls back to context.
    return [
        by_index.get(
            index,
            EvidenceGrade(
                polarity="context",
                rationale="The grader did not return a grade for this candidate.",
                confidence=None,
            ),
        )
        for index in range(1, expected + 1)
    ]


def _polarity(value: object) -> str:
    text = str(value or "").strip().lower()
    return text if text in POLARITIES else "context"


def _confidence(value: object) -> float | None:
    try:
        number = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if number != number:  # NaN
        return None
    return max(0.0, min(1.0, number))


def _trim(text: str, *, limit: int = MAX_EVIDENCE_CHARS) -> str:
    cleaned = " ".join(str(text or "").split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[:limit].rstrip() + "…"
