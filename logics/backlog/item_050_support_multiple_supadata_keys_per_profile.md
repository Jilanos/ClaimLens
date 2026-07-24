## item_050_support_multiple_supadata_keys_per_profile - Support multiple Supadata keys per profile
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
- The current user_api_keys schema supports one key per user/provider, but Supadata rotation requires multiple keys in one profile.
- Adding multi-key support must not regress existing single-key providers.

# Scope
- In:
  - Add a compatible schema migration for multiple Supadata key records with label, priority, enabled state, status, quota metadata, usage counters, and masked fingerprint fields.
  - Keep existing single-key provider APIs working for OpenAI, Semantic Scholar, and NCBI/PubMed.
  - Encrypt Supadata key values with the existing deployment secret.
  - Add helper APIs to save, update, list, reorder, enable/disable, test, and delete Supadata keys.
  - Use GET /v1/me during key test when possible to record maxCredits and usedCredits.
  - Redact Supadata keys anywhere exceptions or UI messages might include request context.
- Out:
  - Sharing Supadata keys across users.
  - Changing OpenAI, Semantic Scholar, or NCBI into multi-key pools unless required by migration compatibility.
  - External secret stores.

# Acceptance criteria
- AC1: A profile can store at least three encrypted Supadata keys with independent labels and priorities.
- AC2: Existing provider rows migrate without data loss and existing API key tests continue to pass.
- AC3: Options/profile UI masks all Supadata keys and never renders plaintext after save.
- AC4: Testing a key calls Supadata account information and stores quota metadata when returned.
- AC5: Tests prove plaintext Supadata keys are absent from SQLite, logs, rendered HTML, and job rows.

# AC Traceability
- request-AC4 -> This backlog slice. Proof: AC1: A profile can store at least three encrypted Supadata keys with independent labels and priorities.
- request-AC5 -> This backlog slice. Proof: AC2: Existing provider rows migrate without data loss and existing API key tests continue to pass.
- request-AC6 -> This backlog slice. Proof: AC3: Options/profile UI masks all Supadata keys and never renders plaintext after save.
- request-AC7 -> This backlog slice. Proof: AC4: Testing a key calls Supadata account information and stores quota metadata when returned.
- request-AC9 -> This backlog slice. Proof: AC5: Tests prove plaintext Supadata keys are absent from SQLite, logs, rendered HTML, and job rows.
- request-AC12 -> This backlog slice. Proof: AC5: Tests prove plaintext Supadata keys are absent from SQLite, logs, rendered HTML, and job rows.
- request-AC13 -> This backlog slice. Proof: AC5: Tests prove plaintext Supadata keys are absent from SQLite, logs, rendered HTML, and job rows.
- request-AC14 -> This backlog slice. Proof: AC5: Tests prove plaintext Supadata keys are absent from SQLite, logs, rendered HTML, and job rows.
- request-AC15 -> This backlog slice. Proof: AC5: Tests prove plaintext Supadata keys are absent from SQLite, logs, rendered HTML, and job rows.
- request-AC8 -> This backlog slice. Evidence needed: On Supadata 402, 429, or account usage where usedCredits >= maxCredits, ClaimLens marks that key exhausted for the current billing period and retries the same native transcript request with the next eligible key.
- request-AC10 -> This backlog slice. Evidence needed: If every Supadata key is exhausted, invalid, missing, or unable to return native captions, the captions step fails with a user-facing message that explains native Supadata captions were unavailable and points to the pasted transcript fallback.
- request-AC11 -> This backlog slice. Evidence needed: Configuration makes transcript provider order explicit, defaulting to the existing local YouTube transcript extraction unless Supadata is enabled for the deployment or user profile.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_008_claimlens_supadata_native_transcript_key_rotation`
- Architecture decision(s): (none yet)
- Request: `req_007_supadata_native_transcript_key_rotation`
- Primary task(s): `task_008_orchestrate_supadata_native_transcript_key_rotation`

# AI Context
- Summary: Support multiple Supadata keys per profile
- Keywords: scaffolded-backlog, support multiple supadata keys per profile, implementation-ready
- Use when: Implementing the scaffolded slice for Support multiple Supadata keys per profile.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.

# Tasks
- `task_008_orchestrate_supadata_native_transcript_key_rotation`

# Notes
- Task `task_008_orchestrate_supadata_native_transcript_key_rotation` was finished via `logics-manager flow finish task` on 2026-07-24.
