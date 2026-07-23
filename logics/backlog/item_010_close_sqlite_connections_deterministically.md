## item_010_close_sqlite_connections_deterministically - Close SQLite connections deterministically
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
- The audit found that `with sqlite3.connect(...) as connection:` commits or rolls back transactions but does not close the connection.
- Repeated CLI usage in later milestones could leak file descriptors if helper functions keep relying on transaction context managers alone.

# Scope
- In:
  - Update SQLite helper functions that open connections to close them deterministically.
  - Preserve existing commit, rollback, schema initialization, and query behavior.
  - Keep the change small and covered by the existing database tests, adding targeted assertions only where they provide real signal.
  - Run the local validation baseline after the change.
- Out:
  - Changing the schema.
  - Adding a database connection pool.
  - Implementing schema migrations.
  - Refactoring unrelated persistence behavior.

# Acceptance criteria
- AC1: Every connection opened by the current database helpers is closed after use.
- AC2: Existing schema initialization and metadata behavior remains unchanged.
- AC3: Existing database tests pass against temporary SQLite databases.
- AC4: `ruff check .` and `pytest` pass locally.

# AC Traceability
- request-AC1 -> This backlog slice. Proof: AC1: Every connection opened by the current database helpers is closed after use.
- request-AC8 -> This backlog slice. Proof: AC2: Existing schema initialization and metadata behavior remains unchanged.
- request-AC3 -> This backlog slice. Evidence needed: Environment override behavior for output-related paths is made consistent or explicitly documented as intentionally limited for the MVP.
- request-AC4 -> This backlog slice. Evidence needed: Malformed numeric configuration values fail with a clear ClaimLens-level error message instead of an opaque conversion exception.
- request-AC5 -> This backlog slice. Evidence needed: A minimal CI workflow runs the established `ruff check .` and `pytest` validation commands on push and pull request events.
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
- Summary: Close SQLite connections deterministically
- Keywords: scaffolded-backlog, close sqlite connections deterministically, implementation-ready
- Use when: Implementing the scaffolded slice for Close SQLite connections deterministically.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Direct audit reliability finding with a small implementation surface and immediate benefit before repeated CLI usage grows.

# Tasks
- `task_003_orchestrate_audit_remediation_and_hardening`

# Notes
- Task `task_003_orchestrate_audit_remediation_and_hardening` was finished via `logics-manager flow finish task` on 2026-07-23.
