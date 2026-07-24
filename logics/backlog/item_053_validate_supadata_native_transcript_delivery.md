## item_053_validate_supadata_native_transcript_delivery - Validate Supadata native transcript delivery
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Medium
> Theme: Validation
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- The Supadata integration touches transcript acquisition, secret storage, schema migrations, UI, and cost controls.
- Closeout needs proof that native-only behavior and key rotation are enforced across boundaries.

# Scope
- In:
  - Add focused tests for client, pipeline, API key storage, DB migration, web Options UI, and documentation examples.
  - Update README and deployment docs with configuration, quota rotation, and failure behavior.
  - Run ruff, pytest, compileall, logics-manager lint --require-status, and logics-manager audit.
  - Record validation output in the orchestration task before closeout.
- Out:
  - Live Supadata calls in CI.
  - VPS deployment execution.
  - Load testing paid Supadata plans.

# Acceptance criteria
- AC1: Tests can run offline with mocked Supadata responses.
- AC2: Validation includes assertions that no code path requests mode=auto or mode=generate.
- AC3: Documentation is specific enough to configure Supadata without reading code.
- AC4: Logics lint and audit pass before closeout.

# AC Traceability
- request-AC5 -> This backlog slice. Proof: AC1: Tests can run offline with mocked Supadata responses.
- request-AC6 -> This backlog slice. Proof: AC2: Validation includes assertions that no code path requests mode=auto or mode=generate.
- request-AC10 -> This backlog slice. Proof: AC3: Documentation is specific enough to configure Supadata without reading code.
- request-AC11 -> This backlog slice. Proof: AC4: Logics lint and audit pass before closeout.
- request-AC12 -> This backlog slice. Proof: AC4: Logics lint and audit pass before closeout.
- request-AC13 -> This backlog slice. Proof: AC4: Logics lint and audit pass before closeout.
- request-AC14 -> This backlog slice. Proof: AC4: Logics lint and audit pass before closeout.
- request-AC15 -> This backlog slice. Proof: AC4: Logics lint and audit pass before closeout.
- request-AC7 -> This backlog slice. Evidence needed: Key selection chooses the first enabled non-exhausted Supadata key by explicit priority, skips keys marked exhausted for the current billing period, and records which key fingerprint was used without storing plaintext.
- request-AC8 -> This backlog slice. Evidence needed: On Supadata 402, 429, or account usage where usedCredits >= maxCredits, ClaimLens marks that key exhausted for the current billing period and retries the same native transcript request with the next eligible key.
- request-AC9 -> This backlog slice. Evidence needed: On Supadata 401, ClaimLens marks the key invalid or test-failed and tries the next eligible key without disabling unrelated providers.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_008_claimlens_supadata_native_transcript_key_rotation`
- Architecture decision(s): (none yet)
- Request: `req_007_supadata_native_transcript_key_rotation`
- Primary task(s): `task_008_orchestrate_supadata_native_transcript_key_rotation`

# AI Context
- Summary: Validate Supadata native transcript delivery
- Keywords: scaffolded-backlog, validate supadata native transcript delivery, implementation-ready
- Use when: Implementing the scaffolded slice for Validate Supadata native transcript delivery.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.

# Tasks
- `task_008_orchestrate_supadata_native_transcript_key_rotation`

# Notes
- Task `task_008_orchestrate_supadata_native_transcript_key_rotation` was finished via `logics-manager flow finish task` on 2026-07-24.
