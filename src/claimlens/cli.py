"""Command line interface for ClaimLens."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from claimlens import __version__
from claimlens.config import load_config
from claimlens.db import init_db

PLACEHOLDER_MESSAGES = {
    "ingest": "YouTube ingestion is planned for Milestone 2.",
    "candidates": "Candidate scoring is planned for Milestone 2.",
    "transcribe": "Transcript creation is planned for Milestone 3.",
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

    for command, message in PLACEHOLDER_MESSAGES.items():
        command_parser = subparsers.add_parser(command, help=message)
        if command in {"transcribe", "analyze", "source-check", "brief"}:
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


def _placeholder(command: str, message: str):
    def run(args: argparse.Namespace) -> int:
        video_id = getattr(args, "video_id", None)
        target = f" for video {video_id}" if video_id else ""
        print(f"`claimlens {command}`{target}: {message}")
        return 0

    return run


if __name__ == "__main__":
    raise SystemExit(main())
