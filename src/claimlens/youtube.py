"""Bounded YouTube helpers for channel discovery and transcript extraction."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

USER_AGENT = "Mozilla/5.0 (compatible; ClaimLens/0.1)"
SUPADATA_BASE_URL = "https://api.supadata.ai/v1"


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


class SupadataError(RuntimeError):
    """Raised when Supadata native transcript extraction cannot continue."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class SupadataAuthError(SupadataError):
    """Raised for invalid Supadata credentials."""


class SupadataQuotaError(SupadataError):
    """Raised when a Supadata key has exhausted available quota."""


class SupadataTranscriptUnavailable(SupadataError):
    """Raised when Supadata native captions are unavailable."""


@dataclass(frozen=True)
class SupadataAccountInfo:
    max_credits: int | None
    used_credits: int | None


class SupadataClient:
    """Small native-only Supadata client."""

    def __init__(self, *, api_key: str, base_url: str = SUPADATA_BASE_URL, timeout: int = 10):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def fetch_native_transcript(
        self,
        *,
        video_url: str,
        video_id: str,
        language: str | None = None,
    ) -> TranscriptResult:
        params = {
            "url": video_url,
            "text": "false",
            "mode": "native",
        }
        if language:
            params["lang"] = language
        body = self._get_json("/transcript", params=params)
        if "jobId" in body:
            raise SupadataTranscriptUnavailable(
                "Supadata returned an asynchronous transcript job; native captions are not ready."
            )
        content = body.get("content")
        if isinstance(content, str):
            text = content.strip()
            if not text:
                raise SupadataTranscriptUnavailable("Supadata native transcript was empty.")
            return TranscriptResult(
                video_id=video_id,
                source="supadata-native",
                language=str(body.get("lang") or language or "unknown"),
                text=text,
                segments=[],
            )
        if not isinstance(content, list) or not content:
            raise SupadataTranscriptUnavailable("Supadata native transcript was unavailable.")

        segments = []
        for item in content:
            if not isinstance(item, dict):
                continue
            segment_text = str(item.get("text") or "").strip()
            if not segment_text:
                continue
            offset = _number(item.get("offset")) or 0.0
            duration = _number(item.get("duration")) or 0.0
            start = offset / 1000.0
            segments.append(
                TranscriptSegment(
                    start_seconds=start,
                    end_seconds=start + (duration / 1000.0),
                    text=segment_text,
                )
            )
        if not segments:
            raise SupadataTranscriptUnavailable("Supadata native transcript had no text segments.")
        return TranscriptResult(
            video_id=video_id,
            source="supadata-native",
            language=str(body.get("lang") or content[0].get("lang") or language or "unknown"),
            text="\n".join(segment.text for segment in segments),
            segments=segments,
        )

    def account_info(self) -> SupadataAccountInfo:
        body = self._get_json("/me", params={})
        return SupadataAccountInfo(
            max_credits=_int_value(body.get("maxCredits")),
            used_credits=_int_value(body.get("usedCredits")),
        )

    def _get_json(self, path: str, *, params: dict[str, str]) -> dict[str, Any]:
        query = f"?{urlencode(params)}" if params else ""
        request = Request(
            f"{self.base_url}{path}{query}",
            headers={
                "User-Agent": USER_AGENT,
                "x-api-key": self.api_key,
                "Accept": "application/json",
            },
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                payload = response.read().decode("utf-8", "ignore")
        except HTTPError as exc:
            self._raise_http_error(exc)
        except Exception as exc:
            raise SupadataError(f"Supadata request failed: {exc}") from exc
        try:
            data = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise SupadataError("Supadata returned invalid JSON.") from exc
        if not isinstance(data, dict):
            raise SupadataError("Supadata returned an unexpected response.")
        return data

    def _raise_http_error(self, exc: HTTPError) -> None:
        message = _supadata_error_message(exc)
        if exc.code == 401:
            raise SupadataAuthError(message, status_code=exc.code) from exc
        if exc.code in {402, 429}:
            raise SupadataQuotaError(message, status_code=exc.code) from exc
        if exc.code in {206, 404}:
            raise SupadataTranscriptUnavailable(message, status_code=exc.code) from exc
        raise SupadataError(message, status_code=exc.code) from exc


def fetch_video_metadata(video_url: str, *, timeout: int = 5) -> YouTubeVideo | None:
    """Return bounded public metadata for a single YouTube URL when oEmbed is available."""

    url = f"https://www.youtube.com/oembed?{urlencode({'url': video_url, 'format': 'json'})}"
    try:
        body = json.loads(_read_url(url, timeout=timeout))
    except Exception:
        return None
    video_id = _video_id_from_url(video_url)
    if not video_id:
        return None
    return YouTubeVideo(
        id=video_id,
        title=body.get("title") or video_id,
        url=video_url,
        published_text=None,
        duration_text=None,
        view_count_text=None,
    )


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


def _read_url(url: str, *, timeout: int = 30) -> str:
    request = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    with urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", "ignore")


def _supadata_error_message(exc: HTTPError) -> str:
    try:
        payload = exc.read().decode("utf-8", "ignore")
        data = json.loads(payload)
    except Exception:
        data = {}
    if isinstance(data, dict):
        for key in ("message", "error", "details"):
            value = data.get(key)
            if value:
                return f"Supadata error {exc.code}: {value}"
    return f"Supadata error {exc.code}"


def _number(value: object) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _int_value(value: object) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _video_id_from_url(video_url: str) -> str | None:
    if "v=" in video_url:
        return video_url.split("v=", 1)[1].split("&", 1)[0]
    return None


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
