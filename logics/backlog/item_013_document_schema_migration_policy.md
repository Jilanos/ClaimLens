## item_013_document_schema_migration_policy - Document schema migration policy
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Low
> Theme: Storage
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- The audit found that `SCHEMA_VERSION` exists but there is no real migration path.
- Before schema version 2, the project needs an explicit rule for when and how migrations are introduced.

# Scope
- In:
  - Document the current schema version behavior.
  - Define the threshold for adding a migration path instead of relying on `CREATE TABLE IF NOT EXISTS`.
  - Specify validation expectations for future schema changes.
  - Add a Logics or roadmap note if future migration work should be scheduled before production data compatibility matters.
- Out:
  - Implementing a migration runner now.
  - Changing `SCHEMA_VERSION`.
  - Changing existing tables.
  - Supporting downgrade migrations.

# Acceptance criteria
- AC1: Project documentation states that schema version 1 is initialization-only.
- AC2: Documentation states that schema version 2 or any destructive/additive production schema change must include a tested migration path.
- AC3: The documented validation baseline includes temporary-database tests for migrations once migrations exist.
- AC4: `logics-manager lint --require-status` passes after the documentation update.

# AC Traceability
- request-AC6 -> This backlog slice. Proof: AC1: Project documentation states that schema version 1 is initialization-only.
- request-AC7 -> This backlog slice. Proof: AC2: Documentation states that schema version 2 or any destructive/additive production schema change must include a tested migration path.
- request-AC8 -> This backlog slice. Proof: AC3: The documented validation baseline includes temporary-database tests for migrations once migrations exist.
- request-AC4 -> This backlog slice. Evidence needed: Malformed numeric configuration values fail with a clear ClaimLens-level error message instead of an opaque conversion exception.
- request-AC5 -> This backlog slice. Evidence needed: A minimal CI workflow runs the established `ruff check .` and `pytest` validation commands on push and pull request events.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_003_claimlens_audit_remediation_and_hardening`
- Architecture decision(s): (none yet)
- Request: `req_002_audit_remediation_and_hardening`
- Primary task(s): `task_003_orchestrate_audit_remediation_and_hardening`

# AI Context
- Summary: Document schema migration policy
- Keywords: scaffolded-backlog, document schema migration policy, implementation-ready
- Use when: Implementing the scaffolded slice for Document schema migration policy.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: Medium
- Rationale: Needed before schema version 2 work, but documentation is enough until an actual schema change is scheduled.

# Tasks
- `task_003_orchestrate_audit_remediation_and_hardening`

# Notes
- Task `task_003_orchestrate_audit_remediation_and_hardening` was finished via `logics-manager flow finish task` on 2026-07-23.
