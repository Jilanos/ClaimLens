## item_003_create_sqlite_schema_and_init_db_command - Create SQLite schema and init-db command
> From version: 1.0.0
> Schema version: 1.0
> Status: Ready
> Understanding: 90%
> Confidence: 85%
> Progress: 0%
> Complexity: Medium
> Theme: Storage
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- The pipeline needs durable local state to avoid duplicate work and to preserve evidence trails.

# Scope
- In:
  - SQLite connection helper.
  - Initial schema creation.
  - Idempotent `claimlens init-db` command.
  - Basic database tests.
- Out:
  - Database migrations beyond initial schema.
  - PostgreSQL support.
  - Production backup tooling.

# Acceptance criteria
- AC1: `claimlens init-db` creates the configured SQLite database.
- AC2: Re-running `claimlens init-db` is idempotent.
- AC3: The initial schema contains all MVP entity tables and key indexes.
- AC4: Tests verify schema creation in a temporary database.

# AC Traceability
- request-AC2 -> This backlog slice. Proof: AC1: `claimlens init-db` creates the configured SQLite database.
- request-AC3 -> This backlog slice. Proof: AC2: Re-running `claimlens init-db` is idempotent.
- request-AC7 -> This backlog slice. Proof: AC3: The initial schema contains all MVP entity tables and key indexes.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_001_claimlens_local_skeleton`
- Architecture decision(s): (none yet)
- Request: `req_000_milestone_1_local_skeleton`
- Primary task(s): `task_001_orchestrate_milestone_1_local_skeleton`

# AI Context
- Summary: Create SQLite schema and init-db command
- Keywords: scaffolded-backlog, create sqlite schema and init-db command, implementation-ready
- Use when: Implementing the scaffolded slice for Create SQLite schema and init-db command.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.
