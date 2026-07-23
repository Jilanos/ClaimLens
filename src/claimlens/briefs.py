"""Markdown brief rendering for the base single-video MVP."""

from __future__ import annotations

import json
from pathlib import Path

from claimlens import db

SOURCE_STATUS = "not_advanced_source_verified"


class BriefError(RuntimeError):
    """Raised when a Markdown brief cannot be generated."""


def render_markdown_brief(
    *,
    video_id: str,
    source_url: str,
    summary: str,
    key_points: list[str],
    notable_claims: list[str],
    caveats: list[str],
    editorial_notes: list[str],
) -> str:
    sections = [
        f"# ClaimLens Brief: {video_id}",
        "",
        f"- Video: {source_url}",
        "- Source verification: Not advanced-source-verified.",
        "- Claim verdicts: Not checked in the base MVP.",
        "",
        "## Summary",
        summary,
        "",
        "## Key Points",
        _bullets(key_points),
        "",
        "## Notable Claims",
        _bullets(notable_claims or ["No notable claims were returned by analysis."]),
        "",
        "## Caveats",
        _bullets(caveats or ["No caveats were returned by analysis."]),
        "",
        "## Editorial Notes",
        _bullets(editorial_notes or ["No editorial notes were returned by analysis."]),
        "",
    ]
    return "\n".join(sections)


def generate_brief(database_path: Path | str, *, video_id: str, briefs_path: Path | str) -> Path:
    analysis = db.latest_analysis(database_path, video_id)
    if analysis is None:
        raise BriefError("Cannot generate a brief before analysis exists.")

    run = db.latest_pipeline_run_for_video(database_path, video_id)
    source_url = run["source_url"] if run is not None and run["source_url"] else video_id
    claims = [row["claim"] for row in db.claims_for_summary(database_path, analysis["id"])]
    details = json.loads(analysis["key_points_json"])

    output_dir = Path(briefs_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{video_id}.md"
    markdown = render_markdown_brief(
        video_id=video_id,
        source_url=source_url,
        summary=analysis["summary"],
        key_points=details.get("key_points", []),
        notable_claims=claims,
        caveats=details.get("caveats", []),
        editorial_notes=details.get("editorial_notes", []),
    )
    output_path.write_text(markdown, encoding="utf-8")
    db.upsert_brief_artifact(
        database_path,
        video_id=video_id,
        summary_id=analysis["id"],
        path=output_path,
        source_verification_status=SOURCE_STATUS,
    )
    return output_path


def _bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)
