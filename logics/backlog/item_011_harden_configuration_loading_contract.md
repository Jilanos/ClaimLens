## item_011_harden_configuration_loading_contract - Harden configuration loading contract
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Medium
> Theme: Configuration
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- The audit found that default config resolution depends on the current working directory.
- Only the database path has an environment override, while output, transcript, and brief paths do not.
- Malformed numeric TOML values currently surface as low-level conversion errors.

# Scope
- In:
  - Choose and implement or document the intended default config path contract.
  - Make output-related path override behavior consistent or explicitly document why only `CLAIMLENS_DB` is supported for the MVP.
  - Wrap malformed numeric configuration values in a clear project-level error.
  - Add focused tests for the chosen config contract and error messages.
  - Update README or config examples when operator behavior changes.
- Out:
  - A full configuration discovery system.
  - Secrets management beyond existing environment variable usage.
  - Runtime channel configuration for ingestion unless required by the existing Milestone 2 chain.
  - A breaking config file format change.

# Acceptance criteria
- AC1: Running from outside the repository either works by documented package-relative defaults or fails with clear documented expectations.
- AC2: Path override behavior is internally consistent and covered by tests or documented as intentionally limited.
- AC3: Invalid integer config values raise a clear ClaimLens configuration error.
- AC4: README or example configuration reflects the final operator contract.
- AC5: `ruff check .` and `pytest` pass locally.

# AC Traceability
- request-AC2 -> This backlog slice. Proof: AC1: Running from outside the repository either works by documented package-relative defaults or fails with clear documented expectations.
- request-AC3 -> This backlog slice. Proof: AC2: Path override behavior is internally consistent and covered by tests or documented as intentionally limited.
- request-AC4 -> This backlog slice. Proof: AC3: Invalid integer config values raise a clear ClaimLens configuration error.
- request-AC7 -> This backlog slice. Proof: AC4: README or example configuration reflects the final operator contract.
- request-AC8 -> This backlog slice. Proof: AC5: `ruff check .` and `pytest` pass locally.
- request-AC6 -> This backlog slice. Evidence needed: Schema versioning expectations are documented before any schema version 2 change, including when migrations are required and how they should be validated.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_003_claimlens_audit_remediation_and_hardening`
- Architecture decision(s): (none yet)
- Request: `req_002_audit_remediation_and_hardening`
- Primary task(s): `task_003_orchestrate_audit_remediation_and_hardening`

# AI Context
- Summary: Harden configuration loading contract
- Keywords: scaffolded-backlog, harden configuration loading contract, implementation-ready
- Use when: Implementing the scaffolded slice for Harden configuration loading contract.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: Medium
- Rationale: Important for installed CLI ergonomics and clear operator failures, but less urgent than connection cleanup and CI.

# Tasks
- `task_003_orchestrate_audit_remediation_and_hardening`

# Notes
- Task `task_003_orchestrate_audit_remediation_and_hardening` was finished via `logics-manager flow finish task` on 2026-07-23.
