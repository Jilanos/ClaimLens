## item_016_add_openai_llm_analysis_for_cleaned_transcripts - Add OpenAI LLM analysis for cleaned transcripts
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Medium
> Theme: LLM analysis
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- The current analyze command is a placeholder.
- The MVP needs a structured analysis output from the cleaned transcript.

# Scope
- In:
  - Add a mockable OpenAI client boundary.
  - Prompt for or read an OpenAI API key at run start.
  - Generate structured summary, key points, notable claims, caveats, and editorial notes.
  - Store analysis output in existing summaries/claims tables or a minimal compatible schema extension.
  - Add tests with mocked OpenAI responses.
- Out:
  - Source retrieval.
  - Evidence verdict labels.
  - Multi-model routing.

# Acceptance criteria
- AC1: Missing OpenAI API key stops before API call with a clear message.
- AC2: Mocked OpenAI analysis stores a summary and notable claims for a video.
- AC3: The prompt contract is documented and covered by tests.
- AC4: Generated analysis does not include the API key in logs or outputs.

# AC Traceability
- request-AC1 -> This backlog slice. Proof: AC1: Missing OpenAI API key stops before API call with a clear message.
- request-AC5 -> This backlog slice. Proof: AC2: Mocked OpenAI analysis stores a summary and notable claims for a video.
- request-AC10 -> This backlog slice. Proof: AC3: The prompt contract is documented and covered by tests.
- request-AC4 -> This backlog slice. Evidence needed: Transcript cleanup stores a timestamp-free, normalized text artifact suitable for LLM input while preserving the raw segmented transcript in SQLite.
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
- Summary: Add OpenAI LLM analysis for cleaned transcripts
- Keywords: scaffolded-backlog, add openai llm analysis for cleaned transcripts, implementation-ready
- Use when: Implementing the scaffolded slice for Add OpenAI LLM analysis for cleaned transcripts.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.

# Notes
- Task `task_004_orchestrate_single_video_local_first_mvp` was finished via `logics-manager flow finish task` on 2026-07-23.
