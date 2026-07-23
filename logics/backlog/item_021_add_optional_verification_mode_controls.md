## item_021_add_optional_verification_mode_controls - Add optional verification mode controls
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Medium
> Theme: Verification activation
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- The existing MVP declares advanced source verification disabled by default but has no executable verification step.
- Operators need an explicit way to run verification without changing base run behavior.

# Scope
- In:
  - Add CLI command or subcommand for running source verification on an analyzed video/run.
  - Add process-page controls for launching the next eligible verification step.
  - Keep advanced_source_verification disabled by default in config.
  - Accept required runtime keys through environment, flags, or HTML form without persistence.
  - Persist verification step status and failure causes in the run state.
- Out:
  - Making verification mandatory for base runs.
  - Batch verification.
  - User account or hosted authentication.

# Acceptance criteria
- AC1: CLI can run verification for a video/run that already has stored analysis.
- AC2: HTML process page exposes verification only when prerequisite analysis exists.
- AC3: Base run behavior remains unchanged when verification is not requested.
- AC4: Missing runtime credentials stop with a clear message and no secret persistence.

# AC Traceability
- request-AC1 -> This backlog slice. Proof: AC1: CLI can run verification for a video/run that already has stored analysis.
- request-AC8 -> This backlog slice. Proof: AC2: HTML process page exposes verification only when prerequisite analysis exists.
- request-AC9 -> This backlog slice. Proof: AC3: Base run behavior remains unchanged when verification is not requested.
- request-AC4 -> This backlog slice. Evidence needed: Each checked claim receives one non-binary verdict: supported, contradicted, mixed, unclear, or not_checked.
- request-AC5 -> This backlog slice. Evidence needed: Each verdict stores cited evidence snippets separated into supporting and contradicting evidence where available.
- request-AC6 -> This backlog slice. Evidence needed: Evidence assessment includes a concise rationale and a human-review disclaimer for health/science outputs.
- request-AC7 -> This backlog slice. Evidence needed: The Markdown brief renderer can produce a source-verified variant with citations, evidence snippets, verdicts, and a visible source-verification status.
- request-AC10 -> This backlog slice. Evidence needed: Tests cover adapter query construction, mocked PubMed/Semantic Scholar responses, source persistence, verdict assessment, verified brief rendering, and HTML process-state rendering without live network calls.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_005_claimlens_advanced_source_verification_mode`
- Architecture decision(s): (none yet)
- Request: `req_004_advanced_source_verification_mode`
- Primary task(s): `task_005_orchestrate_advanced_source_verification_mode`

# AI Context
- Summary: Add optional verification mode controls
- Keywords: scaffolded-backlog, add optional verification mode controls, implementation-ready
- Use when: Implementing the scaffolded slice for Add optional verification mode controls.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.

# Tasks
- `task_005_orchestrate_advanced_source_verification_mode`

# Notes
- Task `task_005_orchestrate_advanced_source_verification_mode` was finished via `logics-manager flow finish task` on 2026-07-23.
