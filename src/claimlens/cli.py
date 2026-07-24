"""Command line interface for ClaimLens."""

from __future__ import annotations

import argparse
import os
from collections.abc import Sequence
from pathlib import Path

from claimlens import __version__
from claimlens.analysis import OpenAIAnalysisClient, analyze_cleaned_transcript
from claimlens.briefs import generate_brief, generate_verified_brief
from claimlens.config import load_config
from claimlens.db import (
    get_pipeline_run,
    init_db,
    set_run_status,
    set_step_status,
    upsert_channel,
    upsert_transcript,
    upsert_video,
)
from claimlens.pipeline import (
    PipelineError,
    clean_run_transcript,
    create_run,
    extract_required_subtitles,
)
from claimlens.verification import VerificationError, default_adapters, verify_sources
from claimlens.web import serve_process_page
from claimlens.youtube import (
    YouTubeError,
    YouTubeVideo,
    fetch_transcript,
)

PLACEHOLDER_MESSAGES = {
    "ingest": "YouTube ingestion is planned for Milestone 2.",
    "candidates": "Candidate scoring is planned for Milestone 2.",
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

    run_video_parser = subparsers.add_parser(
        "run-video",
        help="Create and run the local single-video MVP pipeline.",
    )
    run_video_parser.add_argument("video_url", help="A single YouTube video URL.")
    run_video_parser.add_argument(
        "--database",
        type=Path,
        help="Override the configured SQLite database path.",
    )
    run_video_parser.add_argument(
        "--openai-api-key",
        help="OpenAI API key for analysis. Not persisted.",
    )
    run_video_parser.add_argument(
        "--transcripts-dir",
        type=Path,
        help="Override cleaned transcript output directory.",
    )
    run_video_parser.add_argument(
        "--briefs-dir",
        type=Path,
        help="Override Markdown brief output directory.",
    )
    run_video_parser.add_argument(
        "--report-language",
        help="Language code or label for the final report rendering.",
    )
    run_video_parser.set_defaults(func=_run_video)

    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Analyze a cleaned transcript with OpenAI.",
    )
    analyze_parser.add_argument("video_id", help="YouTube video ID to process.")
    analyze_parser.add_argument("--database", type=Path, help="Override SQLite database path.")
    analyze_parser.add_argument("--openai-api-key", help="OpenAI API key. Not persisted.")
    analyze_parser.add_argument("--max-chars", type=int, help="Override analysis transcript bound.")
    analyze_parser.set_defaults(func=_analyze)

    brief_parser = subparsers.add_parser(
        "brief",
        help="Generate a Markdown brief from stored analysis.",
    )
    brief_parser.add_argument("video_id", help="YouTube video ID to process.")
    brief_parser.add_argument("--database", type=Path, help="Override SQLite database path.")
    brief_parser.add_argument("--briefs-dir", type=Path, help="Override brief output directory.")
    brief_parser.add_argument(
        "--verified",
        action="store_true",
        help="Generate the source-verified brief variant.",
    )
    brief_parser.set_defaults(func=_brief)

    verify_parser = subparsers.add_parser(
        "verify-sources",
        aliases=["source-check"],
        help="Run optional PubMed/Semantic Scholar source verification.",
    )
    verify_parser.add_argument("video_id", help="YouTube video ID to verify.")
    verify_parser.add_argument("--database", type=Path, help="Override SQLite database path.")
    verify_parser.add_argument("--briefs-dir", type=Path, help="Override brief output directory.")
    verify_parser.add_argument("--semantic-scholar-api-key", help="Semantic Scholar API key.")
    verify_parser.add_argument("--ncbi-api-key", help="NCBI/PubMed API key.")
    verify_parser.add_argument(
        "--max-results",
        type=int,
        help="Maximum candidates per adapter and claim.",
    )
    verify_parser.set_defaults(func=_verify_sources)

    serve_parser = subparsers.add_parser("serve", help="Serve the local HTML process page.")
    serve_parser.add_argument("--host", help="Host/interface to bind.")
    serve_parser.add_argument("--port", type=int, help="Port to bind.")
    serve_parser.set_defaults(func=_serve)

    for command, message in PLACEHOLDER_MESSAGES.items():
        command_parser = subparsers.add_parser(command, help=message)
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
        print(
            "Channel page scraping is disabled for the online-readiness MVP; "
            "provide a single YouTube video URL or ID."
        )
        return 1
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


def _run_video(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    database_path = args.database or config.paths.database
    transcripts_dir = args.transcripts_dir or config.paths.transcripts
    briefs_dir = args.briefs_dir or config.paths.briefs
    api_key = args.openai_api_key or config.api_keys.openai

    try:
        run_id = create_run(
            database_path,
            args.video_url,
            report_language=args.report_language or config.pipeline.report_language,
            fetch_metadata=True,
        )
    except PipelineError as exc:
        print(str(exc))
        return 1

    run = None
    try:
        transcript = extract_required_subtitles(database_path, run_id)
        clean_path = clean_run_transcript(database_path, run_id, outputs_path=transcripts_dir)
        print(
            f"Run {run_id}: subtitles extracted for {transcript.video_id}; "
            f"cleaned transcript: {clean_path}"
        )

        run = get_pipeline_run(database_path, run_id)
        if not api_key:
            print("Run paused before analysis: OPENAI_API_KEY is required.")
            return 0

        client = OpenAIAnalysisClient(api_key=api_key)
        set_step_status(database_path, run_id=run_id, step="analysis", status="running")
        summary_id = analyze_cleaned_transcript(
            database_path,
            video_id=run["video_id"],
            client=client,
            max_chars=config.pipeline.analysis_max_chars,
        )
        set_step_status(
            database_path,
            run_id=run_id,
            step="analysis",
            status="succeeded",
            output_path=f"sqlite:summaries/{summary_id}",
        )
        set_run_status(database_path, run_id=run_id, status="running", current_step="brief")
        brief_path = generate_brief(database_path, video_id=run["video_id"], briefs_path=briefs_dir)
        set_step_status(
            database_path,
            run_id=run_id,
            step="brief",
            status="succeeded",
            output_path=str(brief_path),
        )
        set_run_status(database_path, run_id=run_id, status="succeeded", current_step="brief")
        print(f"Run {run_id}: Markdown brief generated: {brief_path}")
        return 0
    except Exception as exc:
        if run is not None:
            set_run_status(
                database_path,
                run_id=run_id,
                status="failed",
                failure_message=str(exc),
            )
        print(f"Run {run_id} failed: {exc}")
        return 1


def _analyze(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    database_path = args.database or config.paths.database
    api_key = args.openai_api_key or config.api_keys.openai
    if not api_key:
        print("OPENAI_API_KEY is required for analysis.")
        return 1

    client = OpenAIAnalysisClient(api_key=api_key)
    summary_id = analyze_cleaned_transcript(
        database_path,
        video_id=args.video_id,
        client=client,
        max_chars=args.max_chars or config.pipeline.analysis_max_chars,
    )
    print(f"Stored analysis for {args.video_id}: summary {summary_id}")
    return 0


def _brief(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    database_path = args.database or config.paths.database
    briefs_dir = args.briefs_dir or config.paths.briefs
    if args.verified:
        path = generate_verified_brief(
            database_path,
            video_id=args.video_id,
            briefs_path=briefs_dir,
        )
    else:
        path = generate_brief(database_path, video_id=args.video_id, briefs_path=briefs_dir)
    print(f"Generated Markdown brief: {path}")
    return 0


def _verify_sources(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    database_path = args.database or config.paths.database
    init_db(database_path)
    adapters = default_adapters(
        semantic_scholar_key=args.semantic_scholar_api_key or config.api_keys.semantic_scholar,
        ncbi_key=args.ncbi_api_key or config.api_keys.ncbi,
    )
    try:
        verification_run_id = verify_sources(
            database_path,
            video_id=args.video_id,
            adapters=adapters,
            max_results=args.max_results or config.pipeline.source_verification_max_results,
            timeout_seconds=config.pipeline.source_verification_timeout_seconds,
        )
        briefs_dir = args.briefs_dir or config.paths.briefs
        path = generate_verified_brief(
            database_path,
            video_id=args.video_id,
            briefs_path=briefs_dir,
        )
    except VerificationError as exc:
        print(str(exc))
        return 1
    print(f"Verified sources for {args.video_id}: verification run {verification_run_id}")
    print(f"Generated source-verified Markdown brief: {path}")
    return 0


def _serve(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    host = args.host or os.environ.get("CLAIMLENS_HOST", "127.0.0.1")
    port = args.port or int(os.environ.get("CLAIMLENS_PORT", "8765"))
    serve_process_page(config, host=host, port=port)
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
