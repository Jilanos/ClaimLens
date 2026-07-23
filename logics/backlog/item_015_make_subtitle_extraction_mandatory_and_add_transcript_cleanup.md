## item_015_make_subtitle_extraction_mandatory_and_add_transcript_cleanup - Make subtitle extraction mandatory and add transcript cleanup
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Medium
> Theme: Transcript pipeline
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- The MVP should not attempt audio transcription fallback.
- LLM input should use cleaned transcript text, not timestamped subtitle segments.

# Scope
- In:
  - Fail the transcript step when no captions are available.
  - Persist user-readable failure causes.
  - Keep raw transcript segments in SQLite for traceability.
  - Generate cleaned transcript text with timestamps removed and obvious ASR noise reduced.
  - Add tests for successful captions and unavailable captions.
- Out:
  - Audio download.
  - Whisper/OpenAI transcription fallback.
  - Heavy grammar correction that changes meaning.

# Acceptance criteria
- AC1: Videos without subtitles stop the pipeline before LLM analysis.
- AC2: The failure page/CLI explains that subtitles are unavailable.
- AC3: Cleaned transcript text contains no timestamp labels.
- AC4: Raw segments remain queryable for audit/debug purposes.

# AC Traceability
- request-AC3 -> This backlog slice. Proof: AC1: Videos without subtitles stop the pipeline before LLM analysis.
- request-AC4 -> This backlog slice. Proof: AC2: The failure page/CLI explains that subtitles are unavailable.
- request-AC10 -> This backlog slice. Proof: AC3: Cleaned transcript text contains no timestamp labels.
- request-AC5 -> This backlog slice. Evidence needed: The LLM step uses OpenAI to produce a concise summary, key points, notable claims, caveats, and editorial notes from the cleaned transcript.
- request-AC6 -> This backlog slice. Evidence needed: The base MVP can generate a reviewable Markdown brief directly after LLM analysis without requiring source retrieval or verdict assessment.
- request-AC7 -> This backlog slice. Evidence needed: The architecture defines an optional advanced source verification mode that can later add source retrieval and claim assessment without blocking the base MVP.
- request-AC8 -> This backlog slice. Evidence needed: A local HTML process page shows the current run, step statuses, failure causes, outputs, and action controls for launching the next eligible step.
- request-AC9 -> This backlog slice. Evidence needed: The implementation remains local-first and VPS-ready: no hardcoded localhost-only assumptions, file paths are configurable, and secrets are not persisted in generated outputs.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_004_claimlens_single_video_local_first_mvp`
- Architecture decision(s): (none yet)
- Request: `req_003_mvp_single_video_local_first_pipeline`
- Primary task(s): `task_004_orchestrate_single_video_local_first_mvp`

# AI Context
- Summary: Make subtitle extraction mandatory and add transcript cleanup
- Keywords: scaffolded-backlog, make subtitle extraction mandatory and add transcript cleanup, implementation-ready
- Use when: Implementing the scaffolded slice for Make subtitle extraction mandatory and add transcript cleanup.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.

# Notes
- Task `task_004_orchestrate_single_video_local_first_mvp` was finished via `logics-manager flow finish task` on 2026-07-23.
