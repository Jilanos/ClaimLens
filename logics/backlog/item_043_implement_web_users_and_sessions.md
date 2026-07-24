## item_043_implement_web_users_and_sessions - Implement web users and sessions
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: High
> Theme: Authentication
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- The current web app has no user identity, session model, or ownership boundary.
- Saving API keys safely requires authenticated user records and access control.

# Scope
- In:
  - Add users table with strong password hashing.
  - Add sessions table or signed/encrypted cookie session model with expiry and rotation.
  - Add login/logout pages and top navigation auth state.
  - Add bootstrap/admin registration policy appropriate for a private self-hosted app.
  - Attach user ownership to runs/jobs/reports where applicable.
  - Test login success/failure, logout, session expiry, secure cookie flags, and ownership checks.
- Out:
  - OAuth/social login.
  - Password reset email.
  - Public registration without operator approval.

# Acceptance criteria
- AC1: A configured operator can create or bootstrap an initial user.
- AC2: Login creates a secure session and logout invalidates it.
- AC3: Navigation reflects guest vs authenticated state.
- AC4: Runs and reports are scoped to the owning user or guest session.
- AC5: Tests cover auth and access-control behavior.

# AC Traceability
- request-AC3 -> This backlog slice. Proof: AC1: A configured operator can create or bootstrap an initial user.
- request-AC4 -> This backlog slice. Proof: AC2: Login creates a secure session and logout invalidates it.
- request-AC10 -> This backlog slice. Proof: AC3: Navigation reflects guest vs authenticated state.
- request-AC12 -> This backlog slice. Proof: AC4: Runs and reports are scoped to the owning user or guest session.
- request-AC14 -> This backlog slice. Proof: AC5: Tests cover auth and access-control behavior.
- request-AC15 -> This backlog slice. Proof: AC5: Tests cover auth and access-control behavior.
- request-AC6 -> This backlog slice. Evidence needed: Saved API keys are encrypted before database persistence using an authenticated encryption scheme and a deployment secret such as CLAIMLENS_KEY_ENCRYPTION_SECRET that is never stored in SQLite; plaintext keys are not logged, rendered, or written to reports/transcripts.
- request-AC7 -> This backlog slice. Evidence needed: Guest users can still create and run processes, but guest-entered keys are used only for the submitted job/action and are not persisted in users, runs, jobs, logs, reports, or transcripts.
- request-AC8 -> This backlog slice. Evidence needed: API key resolution order is explicit and tested: per-request guest key first, authenticated user's saved encrypted key second, server environment/config fallback only if enabled for that deployment, and no key where an adapter supports anonymous use.
- request-AC9 -> This backlog slice. Evidence needed: PubMed and Semantic Scholar verification can run anonymously without stored API keys, while authenticated saved keys are used when present to improve quota/reliability.
- request-AC11 -> This backlog slice. Evidence needed: The web UI supports transcript upload or paste fallback so a deployed VPS remains usable when YouTube blocks transcript fetching from the server IP.
- request-AC13 -> This backlog slice. Evidence needed: Deployment docs include production security guidance: HTTPS only through Caddy, app bound internally, secure cookies, secret generation, backup/restore for SQLite plus encrypted-key secret, and operational warnings about losing CLAIMLENS_KEY_ENCRYPTION_SECRET.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_007_claimlens_deployable_web_auth_and_api_key_management`
- Architecture decision(s): (none yet)
- Request: `req_006_deployable_web_auth_and_api_key_management`
- Primary task(s): `task_007_orchestrate_deployable_web_auth_and_api_key_management`

# AI Context
- Summary: Implement web users and sessions
- Keywords: scaffolded-backlog, implement web users and sessions, implementation-ready
- Use when: Implementing the scaffolded slice for Implement web users and sessions.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.

# Tasks
- `task_007_orchestrate_deployable_web_auth_and_api_key_management`

# Notes
- Task `task_007_orchestrate_deployable_web_auth_and_api_key_management` was finished via `logics-manager flow finish task` on 2026-07-24.
