"""Bounded YouTube helpers for channel discovery and transcript extraction."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.request import Request, urlopen

USER_AGENT = "Mozilla/5.0 (compatible; ClaimLens/0.1)"


@dataclass(frozen=True)
class YouTubeVideo:
    id: str
    title: str
    url: str
    published_text: str | None = None
    duration_text: str | None = None
    view_count_text: str | None = None


@dataclass(frozen=True)
class TranscriptSegment:
    start_seconds: float
    end_seconds: float
    text: str


@dataclass(frozen=True)
class TranscriptResult:
    video_id: str
    source: str
    language: str
    text: str
    segments: list[TranscriptSegment]


class YouTubeError(RuntimeError):
    """Raised when YouTube discovery or transcript extraction fails."""


def latest_channel_videos(channel_url: str, *, limit: int) -> list[YouTubeVideo]:
    """Return the latest visible videos from a YouTube channel videos page."""

    if limit < 1:
        raise ValueError("limit must be greater than zero")

    url = _videos_url(channel_url)
    html = _read_url(url)
    initial_data = _extract_json_object(html, "ytInitialData")
    videos = _extract_videos(initial_data)
    return videos[:limit]


def fetch_transcript(video_id: str, *, languages: list[str] | None = None) -> TranscriptResult:
    """Fetch the preferred transcript for a YouTube video."""

    from youtube_transcript_api import YouTubeTranscriptApi

    transcript = YouTubeTranscriptApi().fetch(video_id, languages=languages or ["en"])
    segments = [
        TranscriptSegment(
            start_seconds=snippet.start,
            end_seconds=snippet.start + snippet.duration,
            text=snippet.text,
        )
        for snippet in transcript
        if snippet.text.strip()
    ]
    text = "\n".join(segment.text for segment in segments)
    source = "youtube-auto" if transcript.is_generated else "youtube"

    return TranscriptResult(
        video_id=video_id,
        source=source,
        language=transcript.language_code,
        text=text,
        segments=segments,
    )


def _videos_url(channel_url: str) -> str:
    base_url = channel_url.rstrip("/")
    return base_url if base_url.endswith("/videos") else f"{base_url}/videos"


def _read_url(url: str) -> str:
    request = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    with urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", "ignore")


def _extract_json_object(html: str, marker: str) -> dict[str, Any]:
    marker_index = html.find(marker)
    if marker_index == -1:
        raise YouTubeError(f"Could not find {marker} in YouTube page")

    start = html.find("{", marker_index)
    if start == -1:
        raise YouTubeError(f"Could not find JSON start for {marker}")

    in_string = False
    escaped = False
    depth = 0

    for index, character in enumerate(html[start:], start):
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
            continue

        if character == '"':
            in_string = True
        elif character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
            if depth == 0:
                return json.loads(html[start : index + 1])

    raise YouTubeError(f"Could not find JSON end for {marker}")


def _extract_videos(data: dict[str, Any]) -> list[YouTubeVideo]:
    videos: list[YouTubeVideo] = []
    seen: set[str] = set()

    for value in _walk(data):
        if isinstance(value, dict) and "lockupViewModel" in value:
            video = _video_from_lockup(value["lockupViewModel"])
        elif isinstance(value, dict) and "videoRenderer" in value:
            video = _video_from_renderer(value["videoRenderer"])
        else:
            continue

        if video and video.id not in seen:
            videos.append(video)
            seen.add(video.id)

    return videos


def _walk(value: Any):
    yield value
    if isinstance(value, dict):
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def _video_from_lockup(lockup: dict[str, Any]) -> YouTubeVideo | None:
    video_id = lockup.get("contentId")
    if not video_id:
        return None

    metadata = lockup.get("metadata", {}).get("lockupMetadataViewModel", {})
    title = metadata.get("title", {}).get("content")
    if not title:
        return None

    parts = _lockup_metadata_parts(metadata)
    duration_text = _lockup_duration(lockup)
    return YouTubeVideo(
        id=video_id,
        title=title,
        url=f"https://www.youtube.com/watch?v={video_id}",
        view_count_text=parts[0] if parts else None,
        published_text=parts[1] if len(parts) > 1 else None,
        duration_text=duration_text,
    )


def _lockup_metadata_parts(metadata: dict[str, Any]) -> list[str]:
    rows = (
        metadata.get("metadata", {})
        .get("contentMetadataViewModel", {})
        .get("metadataRows", [])
    )
    parts: list[str] = []
    for row in rows:
        for part in row.get("metadataParts", []):
            text = part.get("text", {}).get("content")
            if text:
                parts.append(text)
    return parts


def _lockup_duration(lockup: dict[str, Any]) -> str | None:
    overlays = lockup.get("contentImage", {}).get("thumbnailViewModel", {}).get("overlays", [])
    for overlay in overlays:
        badges = overlay.get("thumbnailBottomOverlayViewModel", {}).get("badges", [])
        for badge in badges:
            text = badge.get("thumbnailBadgeViewModel", {}).get("text")
            if text:
                return text
    return None


def _video_from_renderer(renderer: dict[str, Any]) -> YouTubeVideo | None:
    video_id = renderer.get("videoId")
    title = _runs_text(renderer.get("title")) or _simple_text(renderer.get("title"))
    if not video_id or not title:
        return None

    return YouTubeVideo(
        id=video_id,
        title=title,
        url=f"https://www.youtube.com/watch?v={video_id}",
        published_text=_simple_text(renderer.get("publishedTimeText")),
        duration_text=_simple_text(renderer.get("lengthText")),
        view_count_text=_simple_text(renderer.get("viewCountText")),
    )


def _simple_text(value: dict[str, Any] | None) -> str | None:
    if not value:
        return None
    return value.get("simpleText")


def _runs_text(value: dict[str, Any] | None) -> str | None:
    if not value:
        return None
    runs = value.get("runs", [])
    text = "".join(run.get("text", "") for run in runs)
    return text or None
