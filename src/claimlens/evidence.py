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


#: Sources shown to the synthesizer. Enough to describe a literature, still one prompt.
MAX_SYNTHESIS_SOURCES = 8
#: Kept short on purpose: this is a reading aid, not a review article.
MAX_SYNTHESIS_WORDS = 110

SYNTHESIS_SYSTEM_PROMPT = (
    "You write one short paragraph explaining what the supplied scientific records "
    "say about a single claim, for a careful non-specialist reader.\n"
    "You are given the claim, the review verdict, and the records that were "
    "retrieved. Describe the state of the nearby research even when the verdict is "
    "unclear: what the records looked at, whether they point the same way, and how "
    "directly they bear on this claim.\n"
    "Rules:\n"
    "- Say explicitly how close the records are to the claim: whether they address "
    "it directly, address a related question, or only share a topic.\n"
    "- When no record settles the claim, say what the nearby research does show "
    "instead of merely reporting that the verdict is open.\n"
    "- Use only the supplied records. Never add findings, numbers, or citations "
    "from outside them, and never name a record that was not supplied.\n"
    "- Note the limits you can see in the records themselves, such as small or "
    "narrow populations, absent abstracts, or disagreement between records.\n"
    "- Never give diagnosis, treatment, or clinical advice, and never tell the "
    "reader the claim is true or false beyond what the records support.\n"
    f"- Stay under {MAX_SYNTHESIS_WORDS} words, in plain prose without bullet "
    "points or headings.\n"
    'Return JSON only: {"synthesis": "<paragraph>"}.'
)


TRANSLATION_SYSTEM_PROMPT = (
    "You translate short factual claims into English so they can be searched "
    "against scientific literature indexes.\n"
    "Rules:\n"
    "- Return the claim in English. If it is already English, return it "
    "unchanged.\n"
    "- Preserve the meaning exactly: keep every quantity, unit, comparison, "
    "population and hedge. Never strengthen or soften the claim.\n"
    "- Prefer the term a researcher would use in a paper title or abstract, "
    "so the wording matches indexed literature.\n"
    "- Keep proper nouns, molecule names, and acronyms as they are.\n"
    "- Do not explain, comment, or add anything the claim does not state.\n"
    'Return JSON only: {"claims": [{"index": <int>, "english": "<claim>"}]}. '
    "Translate every claim exactly once."
)

#: Language names for the codes the report language field realistically carries.
LANGUAGE_NAMES = {
    "en": "English",
    "fr": "French",
    "es": "Spanish",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "nl": "Dutch",
}


def language_instruction(language: str | None) -> str:
    """Name the prose language, so a French report never gets English commentary."""

    code = (language or "en").strip().lower()
    name = LANGUAGE_NAMES.get(code.split("-")[0], f"the language with IETF tag '{code}'")
    return f"Write every piece of prose you return in {name}."


class EvidenceGradingError(RuntimeError):
    """Raised when the grading boundary cannot return usable grades."""


class EvidenceSynthesisError(RuntimeError):
    """Raised when the synthesis boundary cannot return usable prose."""


class ClaimTranslationError(RuntimeError):
    """Raised when the translation boundary cannot return usable claims."""


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
        language: str = "en",
    ) -> None:
        if not api_key:
            raise EvidenceGradingError("An OpenAI API key is required for evidence grading.")
        self.api_key = api_key
        self.model = model
        self.batch_size = max(1, batch_size)
        self.timeout_seconds = timeout_seconds
        # The judgement is made against English abstracts; only the rationale the
        # reader sees follows the report language.
        self.language = language

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
        content = _chat_json(
            api_key=self.api_key,
            model=self.model,
            system_prompt=f"{SYSTEM_PROMPT}\n{language_instruction(self.language)}",
            user_prompt=build_grading_prompt(claim, candidates),
            timeout_seconds=self.timeout_seconds,
            error=EvidenceGradingError,
            label="Evidence grading",
        )
        return parse_grading_json(content, expected=len(candidates))


@dataclass(frozen=True)
class SynthesisSource:
    """One retrieved record as the synthesizer is allowed to see it."""

    title: str
    evidence_text: str
    #: The grader's polarity, so the paragraph can describe agreement and disagreement.
    polarity: str = "context"
    publisher: str | None = None
    published_at: str | None = None
    adapter: str | None = None
    evidence_text_source: str = "abstract"


class ClaimSynthesizer(Protocol):
    model: str

    def synthesize(self, *, claim: str, verdict: str, sources: list[SynthesisSource]) -> str:
        """Return one paragraph describing what the supplied records say about the claim."""


class OpenAIClaimSynthesizer:
    """Turns graded records into the paragraph a reader needs when a verdict cannot."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str = DEFAULT_MODEL,
        timeout_seconds: int = 60,
        language: str = "en",
    ) -> None:
        if not api_key:
            raise EvidenceSynthesisError("An OpenAI API key is required for claim synthesis.")
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds
        # The records are English; the paragraph belongs to the reader's brief.
        self.language = language

    def synthesize(self, *, claim: str, verdict: str, sources: list[SynthesisSource]) -> str:
        if not sources:
            raise EvidenceSynthesisError("Claim synthesis needs at least one retrieved record.")
        content = _chat_json(
            api_key=self.api_key,
            model=self.model,
            system_prompt=f"{SYNTHESIS_SYSTEM_PROMPT}\n{language_instruction(self.language)}",
            user_prompt=build_synthesis_prompt(claim, verdict, sources),
            timeout_seconds=self.timeout_seconds,
            error=EvidenceSynthesisError,
            label="Claim synthesis",
        )
        return parse_synthesis_json(content)


def build_synthesis_prompt(claim: str, verdict: str, sources: list[SynthesisSource]) -> str:
    lines = [
        f"Claim: {claim.strip()}",
        f"Review verdict so far: {verdict or 'unknown'}",
        "",
        "Retrieved records:",
    ]
    for index, source in enumerate(sources[:MAX_SYNTHESIS_SOURCES], start=1):
        header = f"[{index}] {source.title.strip() or 'Untitled record'}"
        meta = " · ".join(
            part
            for part in (
                source.publisher or None,
                source.published_at or None,
                source.adapter or None,
                f"graded {source.polarity}",
            )
            if part
        )
        lines.append(f"{header} ({meta})")
        if source.evidence_text_source != "abstract":
            lines.append("No abstract available; only the title is shown.")
        lines.append(_trim(source.evidence_text or source.title))
        lines.append("")
    lines.append(
        "Write the paragraph for this claim, describing how directly these records "
        "bear on it."
    )
    return "\n".join(lines)


def parse_synthesis_json(content: str) -> str:
    try:
        raw = json.loads(content)
    except json.JSONDecodeError as exc:
        raise EvidenceSynthesisError("Claim synthesis response was not valid JSON.") from exc
    text = " ".join(str((raw or {}).get("synthesis", "")).split()) if isinstance(raw, dict) else ""
    if not text:
        raise EvidenceSynthesisError("Claim synthesis response carried no paragraph.")
    return text


class ClaimTranslator(Protocol):
    model: str

    def translate(self, *, claims: list[str]) -> list[str]:
        """Return each claim rendered in English, in the order it was given."""


class OpenAIClaimTranslator:
    """Puts claims into the language the literature is indexed in.

    PubMed and Semantic Scholar index English. A French claim searched verbatim
    returns nothing, which reads to the user as "science has no answer" when the real
    cause is that the question was never asked in a language the index understands.
    """

    def __init__(
        self,
        *,
        api_key: str,
        model: str = DEFAULT_MODEL,
        batch_size: int = DEFAULT_BATCH_SIZE,
        timeout_seconds: int = 60,
    ) -> None:
        if not api_key:
            raise ClaimTranslationError("An OpenAI API key is required to translate claims.")
        self.api_key = api_key
        self.model = model
        self.batch_size = max(1, batch_size)
        self.timeout_seconds = timeout_seconds

    def translate(self, *, claims: list[str]) -> list[str]:
        english: list[str] = []
        for start in range(0, len(claims), self.batch_size):
            batch = claims[start : start + self.batch_size]
            content = _chat_json(
                api_key=self.api_key,
                model=self.model,
                system_prompt=TRANSLATION_SYSTEM_PROMPT,
                user_prompt=build_translation_prompt(batch),
                timeout_seconds=self.timeout_seconds,
                error=ClaimTranslationError,
                label="Claim translation",
            )
            english.extend(parse_translation_json(content, originals=batch))
        return english


def build_translation_prompt(claims: list[str]) -> str:
    lines = ["Claims:"]
    for index, claim in enumerate(claims, start=1):
        lines.append(f"[{index}] {_trim(claim, limit=600)}")
    lines.append("")
    lines.append(f"Return all {len(claims)} claims in English.")
    return "\n".join(lines)


def parse_translation_json(content: str, *, originals: list[str]) -> list[str]:
    """Return one English claim per original, falling back to the original text.

    A claim we could not translate is still searchable, just badly; dropping it would
    silently remove it from the verification instead.
    """

    try:
        raw = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ClaimTranslationError("Claim translation response was not valid JSON.") from exc

    entries = raw.get("claims") if isinstance(raw, dict) else None
    if not isinstance(entries, list):
        raise ClaimTranslationError("Claim translation response had no claims array.")

    by_index: dict[int, str] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        try:
            index = int(entry.get("index"))
        except (TypeError, ValueError):
            continue
        english = " ".join(str(entry.get("english", "")).split())
        if 1 <= index <= len(originals) and english and index not in by_index:
            by_index[index] = english

    missing = [index for index in range(1, len(originals) + 1) if index not in by_index]
    if missing:
        LOGGER.info(
            "Claim translation omitted %d claim(s); searching them as written",
            len(missing),
        )
    return [by_index.get(index, originals[index - 1]) for index in range(1, len(originals) + 1)]


def _chat_json(
    *,
    api_key: str,
    model: str,
    system_prompt: str,
    user_prompt: str,
    timeout_seconds: int,
    error: type[RuntimeError],
    label: str,
) -> str:
    """One JSON-mode completion, shared by the grading and synthesis boundaries."""

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0,
    }
    request = Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            body = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise error(f"{label} failed with HTTP {exc.code}.") from exc
    except (URLError, TimeoutError) as exc:
        raise error(
            f"{label} failed because the network request timed out or could not connect."
        ) from exc
    except json.JSONDecodeError as exc:
        raise error(f"{label} response was not valid JSON.") from exc

    try:
        return body["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise error(f"{label} response was missing message content.") from exc


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
