## item_012_add_minimal_ci_quality_gate - Add minimal CI quality gate
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Low
> Theme: Quality
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- The audit found no CI workflow running the repository's established lint and test commands.
- Manual validation is currently easy to skip as implementation work expands.

# Scope
- In:
  - Add a minimal GitHub Actions workflow for supported Python setup.
  - Install project test dependencies using the repository's declared package metadata.
  - Run `ruff check .` and `pytest` on pull request and push events.
  - Keep the workflow deterministic and free of required external secrets.
- Out:
  - Deployment automation.
  - Release publishing.
  - Live YouTube API tests.
  - A full multi-platform CI matrix unless the project metadata already requires it.

# Acceptance criteria
- AC1: `.github/workflows/ci.yml` exists and runs on push and pull request events.
- AC2: The workflow installs dependencies without requiring local-only files or secrets.
- AC3: The workflow runs `ruff check .`.
- AC4: The workflow runs `pytest`.
- AC5: Local `ruff check .` and `pytest` still pass.

# AC Traceability
- request-AC5 -> This backlog slice. Proof: AC1: `.github/workflows/ci.yml` exists and runs on push and pull request events.
- request-AC8 -> This backlog slice. Proof: AC2: The workflow installs dependencies without requiring local-only files or secrets.
- request-AC3 -> This backlog slice. Evidence needed: Environment override behavior for output-related paths is made consistent or explicitly documented as intentionally limited for the MVP.
- request-AC4 -> This backlog slice. Evidence needed: Malformed numeric configuration values fail with a clear ClaimLens-level error message instead of an opaque conversion exception.
- request-AC6 -> This backlog slice. Evidence needed: Schema versioning expectations are documented before any schema version 2 change, including when migrations are required and how they should be validated.
- request-AC7 -> This backlog slice. Evidence needed: README, ROADMAP, or another appropriate project doc reflects any operator-facing changes introduced by the audit response.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_003_claimlens_audit_remediation_and_hardening`
- Architecture decision(s): (none yet)
- Request: `req_002_audit_remediation_and_hardening`
- Primary task(s): `task_003_orchestrate_audit_remediation_and_hardening`

# AI Context
- Summary: Add minimal CI quality gate
- Keywords: scaffolded-backlog, add minimal ci quality gate, implementation-ready
- Use when: Implementing the scaffolded slice for Add minimal CI quality gate.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Establishes the automated validation baseline needed before the audit remediation and Milestone 2 changes expand.

# Tasks
- `task_003_orchestrate_audit_remediation_and_hardening`

# Notes
- Task `task_003_orchestrate_audit_remediation_and_hardening` was finished via `logics-manager flow finish task` on 2026-07-23.
