"""Single-video local-first pipeline orchestration."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from claimlens import db
from claimlens.api_keys import (
    current_billing_period,
    eligible_supadata_keys,
    next_billing_period_start,
)
from claimlens.config import AppConfig
from claimlens.youtube import (
    SupadataAuthError,
    SupadataClient,
    SupadataError,
    SupadataQuotaError,
    SupadataTranscriptUnavailable,
    TranscriptResult,
    YouTubeError,
    YouTubeVideo,
    fetch_transcript,
    fetch_video_metadata,
)

MANUAL_CHANNEL_ID = "manual"
TIMESTAMP_RE = re.compile(
    r"(?:(?:\d{1,2}:)?\d{1,2}:\d{2}(?:\.\d{1,3})?)|(?:\[\s*(?:music|applause)\s*\])",
    re.IGNORECASE,
)
WHITESPACE_RE = re.compile(r"[ \t]+")
SENTENCE_END_RE = re.compile(r"[.!?…][\"'’)]*$")
PARAGRAPH_MIN_CHARS = 280
PARAGRAPH_MAX_CHARS = 600


class PipelineError(RuntimeError):
    """Raised when a local pipeline step cannot continue."""


@dataclass(frozen=True)
class ParsedVideoUrl:
    video_id: str
    canonical_url: str


@dataclass(frozen=True)
class ManualTranscript:
    video_id: str
    source: str
    language: str
    text: str
    segments: list
    submitted_by_user_id: int | None = None
    submitted_by_guest_token: str | None = None


def parse_youtube_video_url(target: str) -> ParsedVideoUrl:
    """Return a single YouTube video ID from supported URL formats."""

    parsed = urlparse(target)
    host = parsed.netloc.lower().removeprefix("www.")
    if not parsed.scheme or host not in {"youtube.com", "m.youtube.com", "youtu.be"}:
        raise PipelineError("Expected a YouTube video URL.")

    video_id: str | None = None
    if host == "youtu.be":
        video_id = parsed.path.strip("/").split("/", 1)[0] or None
    elif parsed.path == "/watch":
        values = parse_qs(parsed.query).get("v", [])
        video_id = values[0] if len(values) == 1 else None
    elif parsed.path.startswith("/shorts/"):
        video_id = parsed.path.split("/shorts/", 1)[1].split("/", 1)[0] or None
    elif parsed.path.startswith("/embed/"):
        video_id = parsed.path.split("/embed/", 1)[1].split("/", 1)[0] or None

    if not video_id or not re.fullmatch(r"[A-Za-z0-9_-]{6,}", video_id):
        raise PipelineError("Could not resolve the URL to exactly one YouTube video ID.")

    return ParsedVideoUrl(
        video_id=video_id,
        canonical_url=f"https://www.youtube.com/watch?v={video_id}",
    )


def create_run(
    database_path: Path | str,
    video_url: str,
    *,
    report_language: str = "en",
    fetch_metadata: bool = False,
    user_id: int | None = None,
    guest_token: str | None = None,
) -> int:
    parsed = parse_youtube_video_url(video_url)
    db.init_db(database_path)
    db.upsert_channel(database_path, channel_id=MANUAL_CHANNEL_ID, title="Manual videos")
    metadata = fetch_video_metadata(parsed.canonical_url) if fetch_metadata else None
    db.upsert_video(
        database_path,
        channel_id=MANUAL_CHANNEL_ID,
        video=metadata
        or YouTubeVideo(
            id=parsed.video_id,
            title=parsed.video_id,
            url=parsed.canonical_url,
        ),
    )
    return db.create_pipeline_run(
        database_path,
        video_id=parsed.video_id,
        source_url=parsed.canonical_url,
        report_language=report_language,
        user_id=user_id,
        guest_token=guest_token,
    )


def extract_required_subtitles(
    database_path: Path | str,
    run_id: int,
    *,
    config: AppConfig | None = None,
    user_id: int | None = None,
) -> TranscriptResult:
    run = _require_run(database_path, run_id)
    video_id = run["video_id"]
    db.set_run_status(database_path, run_id=run_id, status="running", current_step="captions")
    db.set_step_status(database_path, run_id=run_id, step="captions", status="running")

    try:
        transcript = _fetch_configured_transcript(
            database_path,
            run,
            config=config,
            user_id=user_id,
        )
    except Exception as exc:
        message = (
            f"Subtitles are unavailable for video {video_id}; "
            "use the pasted transcript fallback to continue."
        )
        if isinstance(exc, PipelineError) and "YouTube captions unavailable" not in str(exc):
            message = str(exc)
        db.set_step_status(
            database_path,
            run_id=run_id,
            step="captions",
            status="failed",
            failure_message=message,
        )
        db.set_run_status(
            database_path,
            run_id=run_id,
            status="failed",
            current_step="captions",
            failure_message=message,
        )
        raise YouTubeError(message) from exc

    transcript_id = db.upsert_transcript(database_path, transcript)
    db.set_step_status(
        database_path,
        run_id=run_id,
        step="captions",
        status="succeeded",
        output_path=f"sqlite:transcripts/{transcript_id}",
    )
    db.set_run_status(
        database_path,
        run_id=run_id,
        status="running",
        current_step="clean_transcript",
    )
    return transcript


def _fetch_configured_transcript(
    database_path: Path | str,
    run,
    *,
    config: AppConfig | None,
    user_id: int | None,
) -> TranscriptResult:
    provider_order = config.transcripts.provider_order if config else ("youtube",)
    errors: list[str] = []
    for provider in provider_order:
        if provider == "youtube":
            try:
                return fetch_transcript(run["video_id"])
            except Exception as exc:
                errors.append(f"YouTube captions unavailable: {exc}")
                continue
        if provider == "supadata" and config is not None:
            try:
                return _fetch_supadata_native_transcript(
                    database_path,
                    run,
                    config=config,
                    user_id=user_id,
                )
            except PipelineError as exc:
                errors.append(str(exc))
                continue
    if errors:
        raise PipelineError(errors[-1])
    raise PipelineError("No transcript provider is configured.")


def _fetch_supadata_native_transcript(
    database_path: Path | str,
    run,
    *,
    config: AppConfig,
    user_id: int | None,
) -> TranscriptResult:
    if user_id is None:
        raise PipelineError(
            "Supadata native transcript extraction requires a logged-in profile key."
        )
    candidates = eligible_supadata_keys(
        database_path,
        user_id=user_id,
        deployment_secret=config.web.key_encryption_secret,
        monthly_cap=config.transcripts.supadata_monthly_request_cap,
    )
    if not candidates:
        raise PipelineError(
            "No Supadata native transcript key is available with remaining quota; "
            "use the pasted transcript fallback to continue."
        )
    billing_period = current_billing_period()
    final_error = "Supadata native captions were unavailable."
    for candidate in candidates:
        client = SupadataClient(
            api_key=candidate.api_key,
            timeout=config.transcripts.supadata_timeout_seconds,
        )
        try:
            db.mark_supadata_api_key_used(
                database_path,
                user_id=user_id,
                key_id=candidate.id,
                billing_period=billing_period,
            )
            transcript = client.fetch_native_transcript(
                video_url=run["source_url"],
                video_id=run["video_id"],
                language=config.transcripts.supadata_language,
            )
            return transcript
        except SupadataAuthError as exc:
            final_error = "Supadata rejected one saved key."
            db.mark_supadata_api_key_invalid(
                database_path,
                user_id=user_id,
                key_id=candidate.id,
                last_error=str(exc),
            )
        except SupadataQuotaError as exc:
            final_error = "A Supadata key reached its quota."
            db.mark_supadata_api_key_exhausted(
                database_path,
                user_id=user_id,
                key_id=candidate.id,
                exhausted_until=next_billing_period_start(),
                last_error=str(exc),
            )
        except SupadataTranscriptUnavailable as exc:
            final_error = str(exc)
            continue
        except SupadataError as exc:
            final_error = f"Supadata request failed: {exc}"
            continue
    raise PipelineError(
        f"{final_error} No configured Supadata key could fetch native captions; "
        "use the pasted transcript fallback to continue."
    )


def clean_transcript_text(text: str) -> str:
    lines: list[str] = []
    previous = ""
    for raw_line in text.splitlines():
        line = TIMESTAMP_RE.sub(" ", raw_line)
        line = WHITESPACE_RE.sub(" ", line).strip()
        if not line:
            continue
        if line == previous:
            continue
        lines.append(line)
        previous = line
    return _reflow_transcript_paragraphs(" ".join(lines))


def _reflow_transcript_paragraphs(text: str) -> str:
    words = text.split()
    if not words:
        return ""
    paragraphs: list[str] = []
    current: list[str] = []
    for word in words:
        current.append(word)
        candidate = " ".join(current)
        at_sentence_end = bool(SENTENCE_END_RE.search(word))
        reaches_target = len(candidate) >= PARAGRAPH_MIN_CHARS
        exceeds_bound = len(candidate) >= PARAGRAPH_MAX_CHARS
        if exceeds_bound or (at_sentence_end and reaches_target):
            paragraphs.append(candidate)
            current = []
    if current:
        paragraphs.append(" ".join(current))
    return "\n\n".join(paragraphs)


def clean_run_transcript(
    database_path: Path | str,
    run_id: int,
    *,
    outputs_path: Path | str,
) -> Path:
    run = _require_run(database_path, run_id)
    transcript = db.latest_transcript(database_path, run["video_id"])
    if transcript is None:
        raise PipelineError("Cannot clean transcript before subtitles are extracted.")

    db.set_step_status(database_path, run_id=run_id, step="clean_transcript", status="running")
    cleaned = clean_transcript_text(transcript["text"])
    if not cleaned:
        message = "Subtitle cleanup produced an empty transcript."
        db.set_step_status(
            database_path,
            run_id=run_id,
            step="clean_transcript",
            status="failed",
            failure_message=message,
        )
        db.set_run_status(
            database_path,
            run_id=run_id,
            status="failed",
            current_step="clean_transcript",
            failure_message=message,
        )
        raise PipelineError(message)

    output_dir = Path(outputs_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{run['video_id']}.txt"
    output_path.write_text(cleaned + "\n", encoding="utf-8")
    db.upsert_cleaned_transcript(
        database_path,
        video_id=run["video_id"],
        transcript_id=transcript["id"],
        text=cleaned,
        output_path=output_path,
    )
    db.set_step_status(
        database_path,
        run_id=run_id,
        step="clean_transcript",
        status="succeeded",
        output_path=str(output_path),
    )
    db.set_run_status(database_path, run_id=run_id, status="running", current_step="analysis")
    return output_path


def add_manual_transcript(
    database_path: Path | str,
    run_id: int,
    *,
    text: str,
    language: str = "unknown",
    source: str = "user_paste",
    user_id: int | None = None,
    guest_token: str | None = None,
) -> int:
    run = _require_run(database_path, run_id)
    cleaned_text = text.strip()
    if not cleaned_text:
        raise PipelineError("Transcript text is required.")
    transcript_id = db.upsert_transcript(
        database_path,
        ManualTranscript(
            video_id=run["video_id"],
            source=source,
            language=language.strip() or "unknown",
            text=cleaned_text,
            segments=[],
            submitted_by_user_id=user_id,
            submitted_by_guest_token=guest_token,
        ),
    )
    db.set_step_status(
        database_path,
        run_id=run_id,
        step="captions",
        status="succeeded",
        output_path=f"sqlite:transcripts/{transcript_id}",
    )
    db.set_run_status(
        database_path,
        run_id=run_id,
        status="running",
        current_step="clean_transcript",
    )
    return transcript_id


def next_eligible_step(database_path: Path | str, run_id: int) -> str | None:
    steps = {row["step"]: row["status"] for row in db.list_run_steps(database_path, run_id)}
    if steps.get("captions") == "pending":
        return "captions"
    if steps.get("captions") == "succeeded" and steps.get("clean_transcript") == "pending":
        return "clean_transcript"
    if steps.get("clean_transcript") == "succeeded" and steps.get("analysis") == "pending":
        return "analysis"
    if steps.get("analysis") == "succeeded" and steps.get("brief") == "pending":
        return "brief"
    if steps.get("analysis") == "succeeded" and steps.get("source_verification") == "pending":
        return "source_verification"
    return None


def _require_run(database_path: Path | str, run_id: int):
    run = db.get_pipeline_run(database_path, run_id)
    if run is None:
        raise PipelineError(f"Run not found: {run_id}")
    if not run["video_id"]:
        raise PipelineError(f"Run {run_id} does not have a video_id.")
    return run
