## item_052_expose_supadata_profile_key_management_ui - Expose Supadata profile key management UI
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
- Users need to manage several Supadata keys without seeing or leaking saved plaintext secrets.
- Users also need to understand which keys are enabled, exhausted, invalid, or ready without exposing sensitive data.

# Scope
- In:
  - Add Supadata to the authenticated Options/profile page as a multi-key section.
  - Support add, test, enable/disable, reorder, and delete actions with CSRF protection.
  - Show masked key, label, priority, status, last tested, last used, and quota usage when available.
  - Show a native-only transcript note without offering auto or generate controls.
  - Surface all-keys-exhausted messages on the process page with a pasted transcript fallback link or form.
- Out:
  - Showing full keys after save.
  - Letting users choose Supadata auto or generate modes.
  - Admin-wide key pooling.

# Acceptance criteria
- AC1: Authenticated users can manage multiple Supadata keys from the Options/profile UI.
- AC2: The UI never displays a full Supadata key after submission.
- AC3: Disabled and exhausted keys are visibly distinct from ready keys.
- AC4: The process page explains native-caption exhaustion without implying generated transcription will be used.
- AC5: Web tests cover the Supadata key management forms and access control.

# AC Traceability
- request-AC4 -> This backlog slice. Proof: AC1: Authenticated users can manage multiple Supadata keys from the Options/profile UI.
- request-AC6 -> This backlog slice. Proof: AC2: The UI never displays a full Supadata key after submission.
- request-AC7 -> This backlog slice. Proof: AC3: Disabled and exhausted keys are visibly distinct from ready keys.
- request-AC9 -> This backlog slice. Proof: AC4: The process page explains native-caption exhaustion without implying generated transcription will be used.
- request-AC10 -> This backlog slice. Proof: AC5: Web tests cover the Supadata key management forms and access control.
- request-AC13 -> This backlog slice. Proof: AC5: Web tests cover the Supadata key management forms and access control.
- request-AC14 -> This backlog slice. Proof: AC5: Web tests cover the Supadata key management forms and access control.
- request-AC15 -> This backlog slice. Proof: AC5: Web tests cover the Supadata key management forms and access control.
- request-AC8 -> This backlog slice. Evidence needed: On Supadata 402, 429, or account usage where usedCredits >= maxCredits, ClaimLens marks that key exhausted for the current billing period and retries the same native transcript request with the next eligible key.
- request-AC11 -> This backlog slice. Evidence needed: Configuration makes transcript provider order explicit, defaulting to the existing local YouTube transcript extraction unless Supadata is enabled for the deployment or user profile.
- request-AC12 -> This backlog slice. Evidence needed: Supadata free-tier assumptions are configurable, with a default monthly soft cap of 100 requests per key used only as local bookkeeping when /me data is unavailable.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_008_claimlens_supadata_native_transcript_key_rotation`
- Architecture decision(s): (none yet)
- Request: `req_007_supadata_native_transcript_key_rotation`
- Primary task(s): `task_008_orchestrate_supadata_native_transcript_key_rotation`

# AI Context
- Summary: Expose Supadata profile key management UI
- Keywords: scaffolded-backlog, expose supadata profile key management ui, implementation-ready
- Use when: Implementing the scaffolded slice for Expose Supadata profile key management UI.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: Medium
- Rationale: Set by scaffold input or defaulted for grooming.

# Tasks
- `task_008_orchestrate_supadata_native_transcript_key_rotation`

# Notes
- Task `task_008_orchestrate_supadata_native_transcript_key_rotation` was finished via `logics-manager flow finish task` on 2026-07-24.
