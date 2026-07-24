## item_042_specify_paulmondou_infra_integration - Specify paulmondou-infra integration
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Medium
> Theme: Infrastructure integration
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- paulmondou-infra currently serves Kapsule plus static sites; ClaimLens needs a separate dynamic service and Caddy route.
- Deployment must fit the existing archive/git deploy.sh model and Docker Compose conventions.

# Scope
- In:
  - Write the exact intended infra changes for docker-compose.yml, Caddyfile, .env.example, backup.sh, and README.
  - Define CLAIMLENS_DOMAIN and CLAIMLENS_APP_DIR conventions.
  - Define DEPLOY_APP_REPOS example for ClaimLens.
  - Define volume and backup expectations for ClaimLens data.
  - Document Caddy HTTPS/security-header interaction with ClaimLens secure cookies.
- Out:
  - Editing paulmondou-infra unless explicitly requested during implementation.
  - DNS provider automation.

# Acceptance criteria
- AC1: The infra integration plan names every file and environment variable to add or modify.
- AC2: The plan preserves existing Kapsule and static site routes.
- AC3: The deploy command for local archive-mode deployment is documented.
- AC4: Backup and restore implications for encrypted API keys are explicit.

# AC Traceability
- request-AC2 -> This backlog slice. Proof: AC1: The infra integration plan names every file and environment variable to add or modify.
- request-AC13 -> This backlog slice. Proof: AC2: The plan preserves existing Kapsule and static site routes.
- request-AC15 -> This backlog slice. Proof: AC3: The deploy command for local archive-mode deployment is documented.
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
- Summary: Specify paulmondou-infra integration
- Keywords: scaffolded-backlog, specify paulmondou-infra integration, implementation-ready
- Use when: Implementing the scaffolded slice for Specify paulmondou-infra integration.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.

# Tasks
- `task_007_orchestrate_deployable_web_auth_and_api_key_management`

# Notes
- Task `task_007_orchestrate_deployable_web_auth_and_api_key_management` was finished via `logics-manager flow finish task` on 2026-07-24.
