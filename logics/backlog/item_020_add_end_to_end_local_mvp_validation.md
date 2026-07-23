## item_020_add_end_to_end_local_mvp_validation - Add end-to-end local MVP validation
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Medium
> Theme: Validation
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- The MVP needs a reliable proof that one URL can move through the implemented steps.
- Network and paid API calls must be separated from deterministic tests.

# Scope
- In:
  - Add deterministic tests with mocked YouTube and OpenAI boundaries.
  - Add a manual smoke-test recipe for one real YouTube URL with captions.
  - Validate clear failure behavior for missing subtitles and missing OpenAI key.
  - Update README with the new MVP workflow.
- Out:
  - Automated live YouTube/OpenAI tests in CI.
  - Performance tuning for batch workloads.

# Acceptance criteria
- AC1: Unit tests cover all implemented local MVP steps without network access.
- AC2: Manual smoke-test documentation includes one successful URL path and one expected-failure path.
- AC3: README no longer presents channel ingestion as the base MVP path.
- AC4: Lint and tests pass before closeout.

# AC Traceability
- request-AC1 -> This backlog slice. Proof: AC1: Unit tests cover all implemented local MVP steps without network access.
- request-AC2 -> This backlog slice. Proof: AC2: Manual smoke-test documentation includes one successful URL path and one expected-failure path.
- request-AC3 -> This backlog slice. Proof: AC3: README no longer presents channel ingestion as the base MVP path.
- request-AC4 -> This backlog slice. Proof: AC4: Lint and tests pass before closeout.
- request-AC5 -> This backlog slice. Proof: AC4: Lint and tests pass before closeout.
- request-AC6 -> This backlog slice. Proof: AC4: Lint and tests pass before closeout.
- request-AC8 -> This backlog slice. Proof: AC4: Lint and tests pass before closeout.
- request-AC9 -> This backlog slice. Proof: AC4: Lint and tests pass before closeout.
- request-AC10 -> This backlog slice. Proof: AC4: Lint and tests pass before closeout.
- request-AC7 -> This backlog slice. Evidence needed: The architecture defines an optional advanced source verification mode that can later add source retrieval and claim assessment without blocking the base MVP.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_004_claimlens_single_video_local_first_mvp`
- Architecture decision(s): (none yet)
- Request: `req_003_mvp_single_video_local_first_pipeline`
- Primary task(s): `task_004_orchestrate_single_video_local_first_mvp`

# AI Context
- Summary: Add end-to-end local MVP validation
- Keywords: scaffolded-backlog, add end-to-end local mvp validation, implementation-ready
- Use when: Implementing the scaffolded slice for Add end-to-end local MVP validation.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.

# Notes
- Task `task_004_orchestrate_single_video_local_first_mvp` was finished via `logics-manager flow finish task` on 2026-07-23.
