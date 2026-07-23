## item_014_implement_single_video_run_model_and_url_input - Implement single video run model and URL input
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Medium
> Theme: Pipeline foundation
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- The current command surface still implies channel ingestion and video candidate selection.
- The MVP needs a single run entity centered on one YouTube video URL.

# Scope
- In:
  - Add a run-oriented CLI command or adapt existing commands to accept one video URL.
  - Normalize and validate supported YouTube video URL formats.
  - Record run state and step status in SQLite using existing or minimally extended schema.
  - Ensure the OpenAI key is accepted through environment or prompted input without being stored.
- Out:
  - Channel config loading.
  - Candidate scoring.
  - Batch orchestration.

# Acceptance criteria
- AC1: A run can be created from one YouTube video URL.
- AC2: Unsupported or ambiguous URLs fail with a clear message.
- AC3: The run state records the video ID, source URL, current step, and failure details when applicable.
- AC4: The OpenAI key can be supplied at startup without being written to SQLite or outputs.

# AC Traceability
- request-AC1 -> This backlog slice. Proof: AC1: A run can be created from one YouTube video URL.
- request-AC2 -> This backlog slice. Proof: AC2: Unsupported or ambiguous URLs fail with a clear message.
- request-AC9 -> This backlog slice. Proof: AC3: The run state records the video ID, source URL, current step, and failure details when applicable.
- request-AC4 -> This backlog slice. Evidence needed: Transcript cleanup stores a timestamp-free, normalized text artifact suitable for LLM input while preserving the raw segmented transcript in SQLite.
- request-AC5 -> This backlog slice. Evidence needed: The LLM step uses OpenAI to produce a concise summary, key points, notable claims, caveats, and editorial notes from the cleaned transcript.
- request-AC6 -> This backlog slice. Evidence needed: The base MVP can generate a reviewable Markdown brief directly after LLM analysis without requiring source retrieval or verdict assessment.
- request-AC7 -> This backlog slice. Evidence needed: The architecture defines an optional advanced source verification mode that can later add source retrieval and claim assessment without blocking the base MVP.
- request-AC8 -> This backlog slice. Evidence needed: A local HTML process page shows the current run, step statuses, failure causes, outputs, and action controls for launching the next eligible step.
- request-AC10 -> This backlog slice. Evidence needed: Tests cover URL parsing, subtitle-unavailable failure, transcript cleanup, OpenAI client boundaries, brief rendering, and HTML process-state rendering without live network calls.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_004_claimlens_single_video_local_first_mvp`
- Architecture decision(s): (none yet)
- Request: `req_003_mvp_single_video_local_first_pipeline`
- Primary task(s): `task_004_orchestrate_single_video_local_first_mvp`

# AI Context
- Summary: Implement single video run model and URL input
- Keywords: scaffolded-backlog, implement single video run model and url input, implementation-ready
- Use when: Implementing the scaffolded slice for Implement single video run model and URL input.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.

# Notes
- Task `task_004_orchestrate_single_video_local_first_mvp` was finished via `logics-manager flow finish task` on 2026-07-23.
