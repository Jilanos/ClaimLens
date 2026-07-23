"""Command line interface for ClaimLens."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from claimlens import __version__
from claimlens.config import load_config
from claimlens.db import init_db, upsert_channel, upsert_transcript, upsert_video
from claimlens.youtube import YouTubeError, YouTubeVideo, fetch_transcript, latest_channel_videos

PLACEHOLDER_MESSAGES = {
    "ingest": "YouTube ingestion is planned for Milestone 2.",
    "candidates": "Candidate scoring is planned for Milestone 2.",
    "analyze": "Summary and claim extraction are planned for Milestone 3.",
    "source-check": "Evidence source retrieval is planned for Milestone 4.",
    "brief": "Markdown brief generation is planned for Milestone 3.",
    "run-daily": "Daily automation is planned after the repeatable MVP is validated.",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="claimlens",
        description="Turn selected YouTube videos into sourced, claim-aware briefs.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to a ClaimLens TOML config file.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init-db", help="Create or update the local SQLite DB.")
    init_parser.add_argument(
        "--database",
        type=Path,
        help="Override the configured SQLite database path.",
    )
    init_parser.set_defaults(func=_init_db)

    transcribe_parser = subparsers.add_parser(
        "transcribe",
        help="Extract YouTube subtitles for one video or recent videos from a channel.",
    )
    transcribe_parser.add_argument(
        "target",
        help="YouTube video ID, video URL, or channel URL.",
    )
    transcribe_parser.add_argument(
        "--limit",
        type=int,
        default=1,
        help="Number of recent channel videos to process when target is a channel URL.",
    )
    transcribe_parser.add_argument(
        "--database",
        type=Path,
        help="Override the configured SQLite database path.",
    )
    transcribe_parser.set_defaults(func=_transcribe)

    for command, message in PLACEHOLDER_MESSAGES.items():
        command_parser = subparsers.add_parser(command, help=message)
        if command in {"analyze", "source-check", "brief"}:
            command_parser.add_argument("video_id", help="YouTube video ID to process.")
        command_parser.set_defaults(func=_placeholder(command, message))

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


def _init_db(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    database_path = args.database or config.paths.database
    path = init_db(database_path)
    print(f"Initialized ClaimLens database: {path}")
    return 0


def _transcribe(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    database_path = args.database or config.paths.database
    init_db(database_path)

    target = args.target
    channel_url = target if _is_channel_url(target) else None
    channel_id = channel_url or "manual"
    if channel_url:
        videos = latest_channel_videos(channel_url, limit=args.limit)
        upsert_channel(
            database_path,
            channel_id=channel_id,
            title=channel_url,
            url=channel_url,
        )
    else:
        video_id = _video_id(target)
        videos = [
            YouTubeVideo(
                id=video_id,
                title=video_id,
                url=f"https://www.youtube.com/watch?v={video_id}",
            )
        ]
        upsert_channel(database_path, channel_id=channel_id, title="Manual videos")

    processed = 0
    for video in videos:
        upsert_video(database_path, channel_id=channel_id, video=video)
        try:
            transcript = fetch_transcript(video.id)
        except Exception as exc:
            raise YouTubeError(f"Could not fetch transcript for {video.id}: {exc}") from exc

        upsert_transcript(database_path, transcript)
        processed += 1
        print(
            f"Extracted subtitles: {video.id} | {video.title} | "
            f"{len(transcript.segments)} segments | {len(transcript.text)} chars"
        )

    print(f"Stored {processed} transcript(s) in {database_path}")
    return 0


def _is_channel_url(target: str) -> bool:
    return "youtube.com/@" in target or "/channel/" in target or "/c/" in target


def _video_id(target: str) -> str:
    if "watch?v=" in target:
        return target.split("watch?v=", 1)[1].split("&", 1)[0]
    if "youtu.be/" in target:
        return target.rsplit("/", 1)[-1].split("?", 1)[0]
    return target


def _placeholder(command: str, message: str):
    def run(args: argparse.Namespace) -> int:
        video_id = getattr(args, "video_id", None)
        target = f" for video {video_id}" if video_id else ""
        print(f"`claimlens {command}`{target}: {message}")
        return 0

    return run


if __name__ == "__main__":
    raise SystemExit(main())
