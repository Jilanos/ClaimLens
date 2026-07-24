## item_048_version_schema_and_validate_deployable_closeout - Version schema and validate deployable closeout
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
- Auth, sessions, ownership, encrypted keys, and transcript fallback require schema changes beyond v4.
- Deployment readiness needs deterministic tests and operator documentation before any VPS run.

# Scope
- In:
  - Add versioned migrations from schema v4 for users, sessions, encrypted keys, ownership, and transcript fallback.
  - Update README, ROADMAP, config example, and a deployment runbook.
  - Add validation commands and manual smoke-test procedure.
  - Run ruff, pytest, compileall, logics lint, and logics audit before closeout.
- Out:
  - Running the production deployment.
  - Live external API tests in CI.

# Acceptance criteria
- AC1: Schema changes are versioned and tested from v4.
- AC2: Operator docs cover secrets, backup/restore, deployment, and local smoke tests.
- AC3: Automated validation passes.
- AC4: Logics closeout contains AC traceability proofs.

# AC Traceability
- request-AC12 -> This backlog slice. Proof: AC1: Schema changes are versioned and tested from v4.
- request-AC13 -> This backlog slice. Proof: AC2: Operator docs cover secrets, backup/restore, deployment, and local smoke tests.
- request-AC14 -> This backlog slice. Proof: AC3: Automated validation passes.
- request-AC15 -> This backlog slice. Proof: AC4: Logics closeout contains AC traceability proofs.
- request-AC5 -> This backlog slice. Evidence needed: Authenticated users can create, update, mask-display, test, and delete saved API keys for OpenAI, Semantic Scholar, and NCBI/PubMed from an Options page.
- request-AC6 -> This backlog slice. Evidence needed: Saved API keys are encrypted before database persistence using an authenticated encryption scheme and a deployment secret such as CLAIMLENS_KEY_ENCRYPTION_SECRET that is never stored in SQLite; plaintext keys are not logged, rendered, or written to reports/transcripts.
- request-AC7 -> This backlog slice. Evidence needed: Guest users can still create and run processes, but guest-entered keys are used only for the submitted job/action and are not persisted in users, runs, jobs, logs, reports, or transcripts.
- request-AC8 -> This backlog slice. Evidence needed: API key resolution order is explicit and tested: per-request guest key first, authenticated user's saved encrypted key second, server environment/config fallback only if enabled for that deployment, and no key where an adapter supports anonymous use.
- request-AC9 -> This backlog slice. Evidence needed: PubMed and Semantic Scholar verification can run anonymously without stored API keys, while authenticated saved keys are used when present to improve quota/reliability.
- request-AC10 -> This backlog slice. Evidence needed: User ownership and access control are enforced for runs, jobs, reports, transcripts, and options; guests cannot access authenticated users' resources and authenticated users cannot access each other's resources.
- request-AC11 -> This backlog slice. Evidence needed: The web UI supports transcript upload or paste fallback so a deployed VPS remains usable when YouTube blocks transcript fetching from the server IP.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_007_claimlens_deployable_web_auth_and_api_key_management`
- Architecture decision(s): (none yet)
- Request: `req_006_deployable_web_auth_and_api_key_management`
- Primary task(s): `task_007_orchestrate_deployable_web_auth_and_api_key_management`

# AI Context
- Summary: Version schema and validate deployable closeout
- Keywords: scaffolded-backlog, version schema and validate deployable closeout, implementation-ready
- Use when: Implementing the scaffolded slice for Version schema and validate deployable closeout.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.

# Tasks
- `task_007_orchestrate_deployable_web_auth_and_api_key_management`

# Notes
- Task `task_007_orchestrate_deployable_web_auth_and_api_key_management` was finished via `logics-manager flow finish task` on 2026-07-24.
