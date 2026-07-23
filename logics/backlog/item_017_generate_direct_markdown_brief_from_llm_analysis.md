## item_017_generate_direct_markdown_brief_from_llm_analysis - Generate direct Markdown brief from LLM analysis
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Medium
> Theme: Brief generation
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- The refined MVP skips source retrieval and verdict assessment initially.
- Users still need a reviewable output artifact after analysis.

# Scope
- In:
  - Implement brief rendering from video metadata, cleaned transcript status, summary, claims, caveats, and editorial notes.
  - Write outputs to configurable brief paths.
  - Clearly label briefs as not advanced-source-verified unless the optional mode is enabled later.
  - Add snapshot-style tests for brief structure.
- Out:
  - Citation-backed verdicts.
  - CMS publishing.
  - Full HTML report export beyond the process page.

# Acceptance criteria
- AC1: `claimlens brief <video_id>` or the run flow produces `outputs/briefs/<video_id>.md`.
- AC2: The brief includes a visible source-verification status.
- AC3: The brief can be regenerated idempotently.
- AC4: Brief rendering tests run without network access.

# AC Traceability
- request-AC6 -> This backlog slice. Proof: AC1: `claimlens brief <video_id>` or the run flow produces `outputs/briefs/<video_id>.md`.
- request-AC9 -> This backlog slice. Proof: AC2: The brief includes a visible source-verification status.
- request-AC10 -> This backlog slice. Proof: AC3: The brief can be regenerated idempotently.
- request-AC4 -> This backlog slice. Evidence needed: Transcript cleanup stores a timestamp-free, normalized text artifact suitable for LLM input while preserving the raw segmented transcript in SQLite.
- request-AC5 -> This backlog slice. Evidence needed: The LLM step uses OpenAI to produce a concise summary, key points, notable claims, caveats, and editorial notes from the cleaned transcript.
- request-AC7 -> This backlog slice. Evidence needed: The architecture defines an optional advanced source verification mode that can later add source retrieval and claim assessment without blocking the base MVP.
- request-AC8 -> This backlog slice. Evidence needed: A local HTML process page shows the current run, step statuses, failure causes, outputs, and action controls for launching the next eligible step.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_004_claimlens_single_video_local_first_mvp`
- Architecture decision(s): (none yet)
- Request: `req_003_mvp_single_video_local_first_pipeline`
- Primary task(s): `task_004_orchestrate_single_video_local_first_mvp`

# AI Context
- Summary: Generate direct Markdown brief from LLM analysis
- Keywords: scaffolded-backlog, generate direct markdown brief from llm analysis, implementation-ready
- Use when: Implementing the scaffolded slice for Generate direct Markdown brief from LLM analysis.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.

# Notes
- Task `task_004_orchestrate_single_video_local_first_mvp` was finished via `logics-manager flow finish task` on 2026-07-23.
