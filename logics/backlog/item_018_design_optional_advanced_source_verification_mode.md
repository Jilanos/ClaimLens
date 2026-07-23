## item_018_design_optional_advanced_source_verification_mode - Design optional advanced source verification mode
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Medium
> Theme: Advanced verification
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- Source retrieval and claim assessment remain valuable but should not block the base MVP.
- The architecture needs extension points now to avoid a rewrite later.

# Scope
- In:
  - Document the optional `advanced_source_verification` mode.
  - Define source adapters for PubMed, Semantic Scholar, and curated web search as future interfaces.
  - Define how claims move from not-checked to verdict-assessed.
  - Keep base brief generation compatible with later citations and verdicts.
- Out:
  - Implementing live PubMed/Semantic Scholar calls in the base MVP.
  - Automated medical/legal/financial authority claims without human review.

# Acceptance criteria
- AC1: Architecture docs describe how advanced verification plugs into the run after LLM analysis.
- AC2: The base data model can represent source-unverified and source-verified briefs.
- AC3: The option is disabled by default and does not affect base MVP execution.

# AC Traceability
- request-AC7 -> This backlog slice. Proof: AC1: Architecture docs describe how advanced verification plugs into the run after LLM analysis.
- request-AC2 -> This backlog slice. Evidence needed: The pipeline validates that the URL resolves to a single video ID and records a pipeline run state in SQLite.
- request-AC3 -> This backlog slice. Evidence needed: Subtitle extraction succeeds only when YouTube captions are available; otherwise the run stops with a persisted, user-readable failure cause.
- request-AC4 -> This backlog slice. Evidence needed: Transcript cleanup stores a timestamp-free, normalized text artifact suitable for LLM input while preserving the raw segmented transcript in SQLite.
- request-AC5 -> This backlog slice. Evidence needed: The LLM step uses OpenAI to produce a concise summary, key points, notable claims, caveats, and editorial notes from the cleaned transcript.
- request-AC6 -> This backlog slice. Evidence needed: The base MVP can generate a reviewable Markdown brief directly after LLM analysis without requiring source retrieval or verdict assessment.
- request-AC8 -> This backlog slice. Evidence needed: A local HTML process page shows the current run, step statuses, failure causes, outputs, and action controls for launching the next eligible step.
- request-AC9 -> This backlog slice. Evidence needed: The implementation remains local-first and VPS-ready: no hardcoded localhost-only assumptions, file paths are configurable, and secrets are not persisted in generated outputs.
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
- Summary: Design optional advanced source verification mode
- Keywords: scaffolded-backlog, design optional advanced source verification mode, implementation-ready
- Use when: Implementing the scaffolded slice for Design optional advanced source verification mode.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: Medium
- Rationale: Set by scaffold input or defaulted for grooming.

# Notes
- Task `task_004_orchestrate_single_video_local_first_mvp` was finished via `logics-manager flow finish task` on 2026-07-23.
