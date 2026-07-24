## item_046_build_login_navigation_and_options_ui - Build login navigation and options UI
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Medium
> Theme: Web UI
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- The current process page has no global navigation, login page, or user settings area.
- Users need a safe place to manage provider keys without exposing the values.

# Scope
- In:
  - Add a top bar shared by process, report, login, and options pages.
  - Add login/logout affordances.
  - Add Options page with provider key status, masked values, updated timestamps, test/delete actions, and explanatory empty states.
  - Keep guest process forms available for per-action keys.
  - Maintain accessible labels and responsive behavior.
- Out:
  - Full visual redesign beyond the needed navigation/settings surfaces.
  - User profile fields unrelated to auth/key management.

# Acceptance criteria
- AC1: Guest users see Login and per-process key fields.
- AC2: Authenticated users see Options and Logout.
- AC3: Options page can update and delete keys without displaying plaintext.
- AC4: Tests cover rendered guest/authenticated navigation and Options states.

# AC Traceability
- request-AC4 -> This backlog slice. Proof: AC1: Guest users see Login and per-process key fields.
- request-AC5 -> This backlog slice. Proof: AC2: Authenticated users see Options and Logout.
- request-AC7 -> This backlog slice. Proof: AC3: Options page can update and delete keys without displaying plaintext.
- request-AC10 -> This backlog slice. Proof: AC4: Tests cover rendered guest/authenticated navigation and Options states.
- request-AC14 -> This backlog slice. Proof: AC4: Tests cover rendered guest/authenticated navigation and Options states.
- request-AC15 -> This backlog slice. Proof: AC4: Tests cover rendered guest/authenticated navigation and Options states.
- request-AC6 -> This backlog slice. Evidence needed: Saved API keys are encrypted before database persistence using an authenticated encryption scheme and a deployment secret such as CLAIMLENS_KEY_ENCRYPTION_SECRET that is never stored in SQLite; plaintext keys are not logged, rendered, or written to reports/transcripts.
- request-AC8 -> This backlog slice. Evidence needed: API key resolution order is explicit and tested: per-request guest key first, authenticated user's saved encrypted key second, server environment/config fallback only if enabled for that deployment, and no key where an adapter supports anonymous use.
- request-AC9 -> This backlog slice. Evidence needed: PubMed and Semantic Scholar verification can run anonymously without stored API keys, while authenticated saved keys are used when present to improve quota/reliability.
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
- Summary: Build login navigation and options UI
- Keywords: scaffolded-backlog, build login navigation and options ui, implementation-ready
- Use when: Implementing the scaffolded slice for Build login navigation and options UI.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.

# Tasks
- `task_007_orchestrate_deployable_web_auth_and_api_key_management`

# Notes
- Task `task_007_orchestrate_deployable_web_auth_and_api_key_management` was finished via `logics-manager flow finish task` on 2026-07-24.
