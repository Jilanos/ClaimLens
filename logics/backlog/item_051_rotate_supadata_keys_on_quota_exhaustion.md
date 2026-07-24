## item_051_rotate_supadata_keys_on_quota_exhaustion - Rotate Supadata keys on quota exhaustion
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: High
> Theme: Quota management
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- Each free Supadata key can exhaust its monthly request budget, so ClaimLens needs deterministic key selection and failover.
- Retries must be bounded and must not accidentally switch to paid or generated transcript modes.

# Scope
- In:
  - Implement a key-pool selector that picks enabled non-exhausted Supadata keys by priority.
  - Record attempt counts, last used time, last status, usedCredits, maxCredits, and exhausted_until or billing_period marker per key.
  - Mark keys exhausted on 402, 429, or account usage where usedCredits >= maxCredits.
  - Retry the same native transcript request with the next eligible key after quota exhaustion or invalid-key response.
  - Use a configurable default monthly soft cap of 100 native requests per key when Supadata account usage cannot be fetched.
  - Stop after each eligible key has been tried once for a transcript action.
- Out:
  - Circumventing provider limits.
  - Unbounded retry loops.
  - Mixing keys from different users or guest sessions.

# Acceptance criteria
- AC1: Rotation skips exhausted or disabled keys before making Supadata calls.
- AC2: A 429 on the first key retries the same mode=native request with the second key.
- AC3: When all keys are exhausted, the captions step fails once with a clear fallback message.
- AC4: Local monthly soft-cap bookkeeping resets or expires according to a deterministic billing-period policy.
- AC5: Tests cover happy path, quota path, invalid-key path, all-keys-exhausted path, and no-generate invariants.

# AC Traceability
- request-AC7 -> This backlog slice. Proof: AC1: Rotation skips exhausted or disabled keys before making Supadata calls.
- request-AC8 -> This backlog slice. Proof: AC2: A 429 on the first key retries the same mode=native request with the second key.
- request-AC9 -> This backlog slice. Proof: AC3: When all keys are exhausted, the captions step fails once with a clear fallback message.
- request-AC10 -> This backlog slice. Proof: AC4: Local monthly soft-cap bookkeeping resets or expires according to a deterministic billing-period policy.
- request-AC12 -> This backlog slice. Proof: AC5: Tests cover happy path, quota path, invalid-key path, all-keys-exhausted path, and no-generate invariants.
- request-AC13 -> This backlog slice. Proof: AC5: Tests cover happy path, quota path, invalid-key path, all-keys-exhausted path, and no-generate invariants.
- request-AC14 -> This backlog slice. Proof: AC5: Tests cover happy path, quota path, invalid-key path, all-keys-exhausted path, and no-generate invariants.
- request-AC15 -> This backlog slice. Proof: AC5: Tests cover happy path, quota path, invalid-key path, all-keys-exhausted path, and no-generate invariants.
- request-AC6 -> This backlog slice. Evidence needed: Saved Supadata keys are encrypted at rest with the existing deployment secret, never stored in plaintext, never rendered in full, and redacted from exceptions, logs, job payloads, reports, transcripts, and tests.
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
- Summary: Rotate Supadata keys on quota exhaustion
- Keywords: scaffolded-backlog, rotate supadata keys on quota exhaustion, implementation-ready
- Use when: Implementing the scaffolded slice for Rotate Supadata keys on quota exhaustion.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.

# Tasks
- `task_008_orchestrate_supadata_native_transcript_key_rotation`

# Notes
- Task `task_008_orchestrate_supadata_native_transcript_key_rotation` was finished via `logics-manager flow finish task` on 2026-07-24.
