"""Markdown brief rendering for the base single-video MVP."""

from __future__ import annotations

import json
from pathlib import Path

from claimlens import db

SOURCE_STATUS = "not_advanced_source_verified"
VERIFIED_SOURCE_STATUS = "advanced_source_verified"
VERIFICATION_WARNING_STATUS = "advanced_source_verified_with_warnings"


class BriefError(RuntimeError):
    """Raised when a Markdown brief cannot be generated."""


def render_markdown_brief(
    *,
    video_id: str,
    title: str | None = None,
    source_url: str,
    report_language: str = "en",
    metadata: dict[str, str | int | None] | None = None,
    summary: str,
    key_points: list[str],
    notable_claims: list[str],
    caveats: list[str],
    editorial_notes: list[str],
) -> str:
    display_title = title or video_id
    sections = [
        f"# ClaimLens Brief: {display_title}",
        "",
        f"- Video ID: {video_id}",
        f"- Video: {source_url}",
        f"- Report language: {report_language}",
        "- Source verification: Not advanced-source-verified.",
        "- Claim verdicts: Not checked in the base MVP.",
        *_metadata_lines(metadata or {}),
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
    report_language = _report_language(run)
    video = db.get_video(database_path, video_id)
    claims = [row["claim"] for row in db.claims_for_summary(database_path, analysis["id"])]
    details = json.loads(analysis["key_points_json"])

    output_dir = Path(briefs_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{video_id}.md"
    markdown = render_markdown_brief(
        video_id=video_id,
        title=video["title"] if video is not None else None,
        source_url=source_url,
        report_language=report_language,
        metadata=_video_metadata(video),
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


def generate_verified_brief(
    database_path: Path | str,
    *,
    video_id: str,
    briefs_path: Path | str,
) -> Path:
    analysis = db.latest_analysis(database_path, video_id)
    if analysis is None:
        raise BriefError("Cannot generate a verified brief before analysis exists.")
    verification_run = db.latest_verification_run(database_path, video_id)
    if verification_run is None or verification_run["status"] not in {
        "succeeded",
        "completed_with_warnings",
    }:
        raise BriefError("Cannot generate a verified brief before source verification completes.")

    run = db.latest_pipeline_run_for_video(database_path, video_id)
    source_url = run["source_url"] if run is not None and run["source_url"] else video_id
    report_language = _report_language(run)
    video = db.get_video(database_path, video_id)
    details = json.loads(analysis["key_points_json"])
    claims = db.verified_claims_for_summary(database_path, analysis["id"])
    evidence = db.evidence_for_verification(database_path, verification_run["id"])

    output_dir = Path(briefs_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{video_id}.verified.md"
    markdown = render_verified_markdown_brief(
        video_id=video_id,
        title=video["title"] if video is not None else None,
        source_url=source_url,
        report_language=report_language,
        metadata=_video_metadata(video),
        summary=analysis["summary"],
        key_points=details.get("key_points", []),
        claims=claims,
        evidence=evidence,
        verification_status=verification_run["status"],
        adapter_results=_adapter_results(verification_run["source_adapters_json"]),
    )
    output_path.write_text(markdown, encoding="utf-8")
    db.upsert_brief_artifact(
        database_path,
        video_id=video_id,
        summary_id=analysis["id"],
        path=output_path,
        source_verification_status=(
            VERIFIED_SOURCE_STATUS
            if verification_run["status"] == "succeeded"
            else VERIFICATION_WARNING_STATUS
        ),
    )
    return output_path


def render_verified_markdown_brief(
    *,
    video_id: str,
    title: str | None = None,
    source_url: str,
    report_language: str = "en",
    metadata: dict[str, str | int | None] | None = None,
    summary: str,
    key_points: list[str],
    claims: list,
    evidence: list,
    verification_status: str = "succeeded",
    adapter_results: list[dict] | None = None,
) -> str:
    evidence_by_claim: dict[int, list] = {}
    for item in evidence:
        evidence_by_claim.setdefault(item["claim_id"], []).append(item)

    warning = verification_status == "completed_with_warnings"
    verification_label = (
        "Advanced-source verification completed with warnings."
        if warning
        else "Advanced-source-verified with PubMed/Semantic Scholar candidates."
    )
    sections = [
        f"# ClaimLens Source-Verified Brief: {title or video_id}",
        "",
        f"- Video ID: {video_id}",
        f"- Video: {source_url}",
        f"- Report language: {report_language}",
        f"- Source verification: {verification_label}",
        "- Review status: Human review required for health/science claims.",
        *_metadata_lines(metadata or {}),
        "",
        "## Summary",
        summary,
        "",
        "## Key Points",
        _bullets(key_points),
        "",
        "## Checked Claims",
    ]
    for claim in claims:
        sections.extend(_claim_section(claim, evidence_by_claim.get(claim["id"], [])))
    sections.extend(
        [
            "",
            "## Adapter outcomes",
            _adapter_outcome_bullets(adapter_results or []),
            "",
            "## Human Review Disclaimer",
            (
                "This source verification is an editorial aid for health/science review. "
                "It does not replace expert judgment, clinical guidance, diagnosis, "
                "or medical advice."
            ),
            "",
        ]
    )
    return "\n".join(sections)


def _bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def _video_metadata(video) -> dict[str, str | int | None]:
    if video is None:
        return {}
    return {
        "Channel": video["channel_title"],
        "Published": video["published_at"],
        "Duration seconds": video["duration_seconds"],
        "Views": video["view_count"],
    }


def _report_language(run) -> str:
    if run is None or "report_language" not in run.keys() or not run["report_language"]:
        return "en"
    return str(run["report_language"])


def _metadata_lines(metadata: dict[str, str | int | None]) -> list[str]:
    lines = []
    for label, value in metadata.items():
        if value is not None and value != "":
            lines.append(f"- {label}: {value}")
    return lines


def _claim_section(claim, evidence: list) -> list[str]:
    supporting = [item for item in evidence if item["polarity"] == "supports"]
    contradicting = [item for item in evidence if item["polarity"] == "contradicts"]
    section = [
        "",
        f"### {claim['claim']}",
        f"- Verdict: {claim['verdict']}",
        f"- Transcript excerpt: {claim['transcript_excerpt'] or 'No excerpt stored.'}",
        f"- Rationale: {claim['rationale'] or 'No rationale stored.'}",
        "",
        "Supporting evidence:",
        _evidence_bullets(supporting),
        "",
        "Contradicting evidence:",
        _evidence_bullets(contradicting),
    ]
    return section


def _evidence_bullets(items: list) -> str:
    if not items:
        return "- None recorded."
    return "\n".join(
        (
            f"- \"{item['snippet']}\" "
            f"([{item['source_title']}]({item['source_url']}), {item['source_adapter']})"
        )
        for item in items
    )


def _adapter_outcome_bullets(items: list[dict]) -> str:
    if not items:
        return "- No adapter outcome was recorded."
    return "\n".join(
        f"- {item.get('adapter', 'unknown')}: {item.get('status', 'unknown')}"
        + (
            f" ({item['message']})"
            if item.get("message")
            else f" ({item.get('candidate_count', 0)} candidates)"
        )
        for item in items
    )


def _adapter_results(raw_value: str | None) -> list[dict]:
    try:
        raw = json.loads(raw_value or "[]")
    except json.JSONDecodeError:
        return []
    if not isinstance(raw, list):
        return []
    return [
        item
        if isinstance(item, dict)
        else {"adapter": str(item), "status": "unknown", "candidate_count": 0}
        for item in raw
    ]
