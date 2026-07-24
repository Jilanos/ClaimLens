## item_041_package_claimlens_for_container_deployment - Package ClaimLens for container deployment
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Medium
> Theme: Deployment packaging
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- ClaimLens currently runs as a local Python CLI/web process and does not yet define a production container runtime.
- The existing VPS infra expects deployable app directories and Docker Compose services.

# Scope
- In:
  - Add a Dockerfile or equivalent deployable runtime entrypoint for ClaimLens.
  - Define production environment variables, internal host/port, data volume paths, and healthcheck behavior.
  - Document secret generation and persistent path layout for SQLite, outputs, transcripts, briefs, and logs.
  - Keep the app listening only on an internal interface/container port behind Caddy.
- Out:
  - Actually running the deployment on the VPS.
  - Changing Kapsule's runtime behavior.

# Acceptance criteria
- AC1: A local container build can start ClaimLens web mode with persistent data paths.
- AC2: A healthcheck or smoke endpoint exists for Compose/Caddy diagnostics.
- AC3: Production env variables are documented and covered by config tests.
- AC4: The runtime does not require secrets to be committed.

# AC Traceability
- request-AC1 -> This backlog slice. Proof: AC1: A local container build can start ClaimLens web mode with persistent data paths.
- request-AC13 -> This backlog slice. Proof: AC2: A healthcheck or smoke endpoint exists for Compose/Caddy diagnostics.
- request-AC15 -> This backlog slice. Proof: AC3: Production env variables are documented and covered by config tests.
- request-AC4 -> This backlog slice. Evidence needed: The top navigation bar shows application navigation and auth state, including login/logout and an authenticated Options link.
- request-AC5 -> This backlog slice. Evidence needed: Authenticated users can create, update, mask-display, test, and delete saved API keys for OpenAI, Semantic Scholar, and NCBI/PubMed from an Options page.
- request-AC6 -> This backlog slice. Evidence needed: Saved API keys are encrypted before database persistence using an authenticated encryption scheme and a deployment secret such as CLAIMLENS_KEY_ENCRYPTION_SECRET that is never stored in SQLite; plaintext keys are not logged, rendered, or written to reports/transcripts.
- request-AC7 -> This backlog slice. Evidence needed: Guest users can still create and run processes, but guest-entered keys are used only for the submitted job/action and are not persisted in users, runs, jobs, logs, reports, or transcripts.
- request-AC8 -> This backlog slice. Evidence needed: API key resolution order is explicit and tested: per-request guest key first, authenticated user's saved encrypted key second, server environment/config fallback only if enabled for that deployment, and no key where an adapter supports anonymous use.
- request-AC9 -> This backlog slice. Evidence needed: PubMed and Semantic Scholar verification can run anonymously without stored API keys, while authenticated saved keys are used when present to improve quota/reliability.
- request-AC10 -> This backlog slice. Evidence needed: User ownership and access control are enforced for runs, jobs, reports, transcripts, and options; guests cannot access authenticated users' resources and authenticated users cannot access each other's resources.
- request-AC11 -> This backlog slice. Evidence needed: The web UI supports transcript upload or paste fallback so a deployed VPS remains usable when YouTube blocks transcript fetching from the server IP.
- request-AC12 -> This backlog slice. Evidence needed: Database schema migrations add users, sessions, encrypted API keys, ownership fields, and transcript fallback records through versioned, tested migration steps from schema v4.
- request-AC14 -> This backlog slice. Evidence needed: Tests cover auth, session security flags, API key encryption/decryption and redaction, guest key non-persistence, key resolution order, anonymous PubMed/Semantic behavior, access control, transcript upload fallback, and report access.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_007_claimlens_deployable_web_auth_and_api_key_management`
- Architecture decision(s): (none yet)
- Request: `req_006_deployable_web_auth_and_api_key_management`
- Primary task(s): `task_007_orchestrate_deployable_web_auth_and_api_key_management`

# AI Context
- Summary: Package ClaimLens for container deployment
- Keywords: scaffolded-backlog, package claimlens for container deployment, implementation-ready
- Use when: Implementing the scaffolded slice for Package ClaimLens for container deployment.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.

# Tasks
- `task_007_orchestrate_deployable_web_auth_and_api_key_management`

# Notes
- Task `task_007_orchestrate_deployable_web_auth_and_api_key_management` was finished via `logics-manager flow finish task` on 2026-07-24.
