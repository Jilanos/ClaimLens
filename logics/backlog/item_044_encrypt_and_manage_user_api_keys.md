## item_044_encrypt_and_manage_user_api_keys - Encrypt and manage user API keys
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: High
> Theme: Secret management
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- Authenticated users need reusable API keys, but API keys must not be stored or displayed in plaintext.
- The application must also work without PubMed/Semantic Scholar keys.

# Scope
- In:
  - Add encrypted_api_keys or equivalent table keyed by user and provider.
  - Use authenticated encryption with per-record nonce/salt and a deployment secret outside SQLite.
  - Support providers: OpenAI, Semantic Scholar, and NCBI/PubMed.
  - Add Options page controls to add, update, test, mask, and delete keys.
  - Implement redaction for logs, HTML, jobs, reports, and exceptions.
  - Implement and test API key resolution order.
- Out:
  - Hardware security modules or external secret stores.
  - Sharing keys between users.
  - Persisting guest keys.

# Acceptance criteria
- AC1: Stored key material is encrypted and cannot be read from SQLite without CLAIMLENS_KEY_ENCRYPTION_SECRET.
- AC2: Key values are never rendered back except as masked metadata.
- AC3: Guest keys are not persisted.
- AC4: PubMed/Semantic Scholar run anonymously when no key is available.
- AC5: Tests cover encryption, redaction, deletion, and resolution order.

# AC Traceability
- request-AC5 -> This backlog slice. Proof: AC1: Stored key material is encrypted and cannot be read from SQLite without CLAIMLENS_KEY_ENCRYPTION_SECRET.
- request-AC6 -> This backlog slice. Proof: AC2: Key values are never rendered back except as masked metadata.
- request-AC8 -> This backlog slice. Proof: AC3: Guest keys are not persisted.
- request-AC9 -> This backlog slice. Proof: AC4: PubMed/Semantic Scholar run anonymously when no key is available.
- request-AC12 -> This backlog slice. Proof: AC5: Tests cover encryption, redaction, deletion, and resolution order.
- request-AC14 -> This backlog slice. Proof: AC5: Tests cover encryption, redaction, deletion, and resolution order.
- request-AC15 -> This backlog slice. Proof: AC5: Tests cover encryption, redaction, deletion, and resolution order.
- request-AC7 -> This backlog slice. Evidence needed: Guest users can still create and run processes, but guest-entered keys are used only for the submitted job/action and are not persisted in users, runs, jobs, logs, reports, or transcripts.
- request-AC10 -> This backlog slice. Evidence needed: User ownership and access control are enforced for runs, jobs, reports, transcripts, and options; guests cannot access authenticated users' resources and authenticated users cannot access each other's resources.
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
- Summary: Encrypt and manage user API keys
- Keywords: scaffolded-backlog, encrypt and manage user api keys, implementation-ready
- Use when: Implementing the scaffolded slice for Encrypt and manage user API keys.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.

# Tasks
- `task_007_orchestrate_deployable_web_auth_and_api_key_management`

# Notes
- Task `task_007_orchestrate_deployable_web_auth_and_api_key_management` was finished via `logics-manager flow finish task` on 2026-07-24.
