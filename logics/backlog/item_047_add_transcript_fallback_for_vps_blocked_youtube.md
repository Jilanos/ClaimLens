## item_047_add_transcript_fallback_for_vps_blocked_youtube - Add transcript fallback for VPS-blocked YouTube
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Medium
> Theme: Transcript acquisition
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- YouTube can block transcript fetching from VPS or datacenter IPs, making a deployed app unusable if server-side fetching is the only transcript path.
- The current failure path is clear but still stops the user.

# Scope
- In:
  - Add web fallback to paste transcript text or upload .txt/.srt/.vtt after captions fail or before attempting YouTube fetch.
  - Normalize uploaded/pasted transcripts into the existing transcript and cleanup pipeline.
  - Persist transcript source as user_upload or user_paste with ownership/audit metadata.
  - Document deployed behavior and manual local smoke tests.
- Out:
  - Proxy rotation or paid transcript scraping services.
  - Audio download/transcription fallback.

# Acceptance criteria
- AC1: A user can continue a run using pasted/uploaded transcript text when YouTube captions are blocked.
- AC2: Uploaded/pasted transcript data follows the same cleanup, analysis, report, and verification flow.
- AC3: Tests cover paste/upload fallback and ownership.
- AC4: Docs explain this is the supported VPS fallback.

# AC Traceability
- request-AC11 -> This backlog slice. Proof: AC1: A user can continue a run using pasted/uploaded transcript text when YouTube captions are blocked.
- request-AC12 -> This backlog slice. Proof: AC2: Uploaded/pasted transcript data follows the same cleanup, analysis, report, and verification flow.
- request-AC14 -> This backlog slice. Proof: AC3: Tests cover paste/upload fallback and ownership.
- request-AC15 -> This backlog slice. Proof: AC4: Docs explain this is the supported VPS fallback.
- request-AC5 -> This backlog slice. Evidence needed: Authenticated users can create, update, mask-display, test, and delete saved API keys for OpenAI, Semantic Scholar, and NCBI/PubMed from an Options page.
- request-AC6 -> This backlog slice. Evidence needed: Saved API keys are encrypted before database persistence using an authenticated encryption scheme and a deployment secret such as CLAIMLENS_KEY_ENCRYPTION_SECRET that is never stored in SQLite; plaintext keys are not logged, rendered, or written to reports/transcripts.
- request-AC7 -> This backlog slice. Evidence needed: Guest users can still create and run processes, but guest-entered keys are used only for the submitted job/action and are not persisted in users, runs, jobs, logs, reports, or transcripts.
- request-AC8 -> This backlog slice. Evidence needed: API key resolution order is explicit and tested: per-request guest key first, authenticated user's saved encrypted key second, server environment/config fallback only if enabled for that deployment, and no key where an adapter supports anonymous use.
- request-AC9 -> This backlog slice. Evidence needed: PubMed and Semantic Scholar verification can run anonymously without stored API keys, while authenticated saved keys are used when present to improve quota/reliability.
- request-AC10 -> This backlog slice. Evidence needed: User ownership and access control are enforced for runs, jobs, reports, transcripts, and options; guests cannot access authenticated users' resources and authenticated users cannot access each other's resources.
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
- Summary: Add transcript fallback for VPS-blocked YouTube
- Keywords: scaffolded-backlog, add transcript fallback for vps-blocked youtube, implementation-ready
- Use when: Implementing the scaffolded slice for Add transcript fallback for VPS-blocked YouTube.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.

# Tasks
- `task_007_orchestrate_deployable_web_auth_and_api_key_management`

# Notes
- Task `task_007_orchestrate_deployable_web_auth_and_api_key_management` was finished via `logics-manager flow finish task` on 2026-07-24.
