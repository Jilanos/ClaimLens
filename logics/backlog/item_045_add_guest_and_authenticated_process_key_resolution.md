## item_045_add_guest_and_authenticated_process_key_resolution - Add guest and authenticated process key resolution
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Medium
> Theme: Process execution
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- Current process forms accept per-action keys but do not distinguish guest, authenticated saved key, or server fallback semantics.
- Jobs must not persist transient guest secrets.

# Scope
- In:
  - Create a key-provider boundary that resolves keys from request, authenticated user storage, optional server config, or anonymous adapter support.
  - Pass transient keys into queued jobs without storing plaintext in job rows.
  - Ensure source verification adapters are instantiated without keys when keys are unavailable.
  - Return controlled prompts when OpenAI analysis cannot run because no key exists.
- Out:
  - Server-wide billing/quota accounting.
  - Full SaaS tenant administration.

# Acceptance criteria
- AC1: Guest process keys work for one action and are not persisted.
- AC2: Authenticated saved keys are used when no per-request key is supplied.
- AC3: OpenAI analysis fails clearly when no OpenAI key is available.
- AC4: PubMed/Semantic Scholar verification still runs without keys.
- AC5: Tests cover all key resolution branches.

# AC Traceability
- request-AC7 -> This backlog slice. Proof: AC1: Guest process keys work for one action and are not persisted.
- request-AC8 -> This backlog slice. Proof: AC2: Authenticated saved keys are used when no per-request key is supplied.
- request-AC9 -> This backlog slice. Proof: AC3: OpenAI analysis fails clearly when no OpenAI key is available.
- request-AC10 -> This backlog slice. Proof: AC4: PubMed/Semantic Scholar verification still runs without keys.
- request-AC14 -> This backlog slice. Proof: AC5: Tests cover all key resolution branches.
- request-AC15 -> This backlog slice. Proof: AC5: Tests cover all key resolution branches.
- request-AC6 -> This backlog slice. Evidence needed: Saved API keys are encrypted before database persistence using an authenticated encryption scheme and a deployment secret such as CLAIMLENS_KEY_ENCRYPTION_SECRET that is never stored in SQLite; plaintext keys are not logged, rendered, or written to reports/transcripts.
- request-AC11 -> This backlog slice. Evidence needed: The web UI supports transcript upload or paste fallback so a deployed VPS remains usable when YouTube blocks transcript fetching from the server IP.
- request-AC12 -> This backlog slice. Evidence needed: Database schema migrations add users, sessions, encrypted API keys, ownership fields, and transcript fallback records through versioned, tested migration steps from schema v4.
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
- Summary: Add guest and authenticated process key resolution
- Keywords: scaffolded-backlog, add guest and authenticated process key resolution, implementation-ready
- Use when: Implementing the scaffolded slice for Add guest and authenticated process key resolution.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.

# Tasks
- `task_007_orchestrate_deployable_web_auth_and_api_key_management`

# Notes
- Task `task_007_orchestrate_deployable_web_auth_and_api_key_management` was finished via `logics-manager flow finish task` on 2026-07-24.
