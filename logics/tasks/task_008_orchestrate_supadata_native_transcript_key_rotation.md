## task_008_orchestrate_supadata_native_transcript_key_rotation - Orchestrate Supadata Native Transcript Key Rotation
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Medium
> Theme: Implementation delivery
> Reminder: Update status/understanding/confidence/progress and linked request/backlog references when you edit this doc.
> Owner: codex

# Context
- Orchestrate the scaffolded request chain and keep sibling implementation slices linked.

# Plan
- [x] 1. Confirm Supadata API contract and lock ClaimLens to native transcript mode only.
- [x] 2. Design the schema migration for multiple Supadata keys per authenticated profile while preserving existing single-key providers.
- [x] 3. Implement Supadata native transcript client and provider-order configuration.
- [x] 4. Implement encrypted Supadata key pool persistence, testing, quota metadata, and redaction.
- [x] 5. Implement deterministic key selection and rotation on exhausted, invalid, or quota-limited keys.
- [x] 6. Wire Supadata native transcript extraction into the pipeline and web process actions.
- [x] 7. Extend the Options/profile UI for multiple Supadata keys and quota/status visibility.
- [x] 8. Update README, deployment docs, and offline smoke-test notes.
- [x] 9. Validate with ruff, pytest, compileall, logics-manager lint --require-status, and logics-manager audit.
- [x] 10. ADR 009 checkpoint: update affected Logics docs during each meaningful wave and leave the repo commit-ready; commit creation remains under operator control.
- [x] 11. GATE: do not close until native-only Supadata behavior, key encryption, quota rotation, and migration compatibility have test evidence.
- [x] ADR 009 checkpoint: update affected Logics docs during each meaningful wave and leave the repo commit-ready.
- [x] Keep commit creation under operator control; do not force one commit per micro-step.
- [x] GATE: do not close until lint, audit, and scaffold validation pass.

# Backlog
- `item_049_implement_supadata_native_transcript_client`
- `item_050_support_multiple_supadata_keys_per_profile`
- `item_051_rotate_supadata_keys_on_quota_exhaustion`
- `item_052_expose_supadata_profile_key_management_ui`
- `item_053_validate_supadata_native_transcript_delivery`

# Definition of Done (DoD)
- [x] Generated request, product, backlog, and task docs are present.
- [x] Context-pack handoff is available when requested.
- [x] Validation passes.
- [x] Meaningful waves followed ADR 009: affected docs updated and the repo left commit-ready without automatic commits.

# AC Traceability
- request-AC1 -> This task. Proof: `src/claimlens/youtube.py:SupadataClient.fetch_native_transcript` calls `GET /v1/transcript` with `x-api-key`, `url`, optional `lang`, `text=false`, and `mode=native`; `tests/test_youtube.py` asserts the request.
- request-AC2 -> This task. Proof: `SupadataClient` converts Supadata `offset`/`duration` milliseconds to `TranscriptSegment` seconds; covered in `tests/test_youtube.py`.
- request-AC3 -> This task. Proof: Supadata mode is hardcoded to `native`; config only accepts `youtube` and `supadata`; Options text exposes no auto/generate controls; tests assert no `mode=auto` or `mode=generate`.
- request-AC4 -> This task. Proof: `src/claimlens/web.py:render_options_page` renders a Supadata multi-key section with add, update, enable/disable, test, and delete actions.
- request-AC5 -> This task. Proof: Existing `user_api_keys` and `resolve_api_key` behavior remains unchanged; tests for OpenAI, Semantic Scholar, and NCBI-compatible resolution still pass.
- request-AC6 -> This task. Proof: `src/claimlens/api_keys.py:save_supadata_api_key` encrypts keys with the existing deployment secret and tests assert plaintext is absent from SQLite and rendered HTML.
- request-AC7 -> This task. Proof: `eligible_supadata_keys` and `db.list_eligible_supadata_api_keys` select enabled non-exhausted keys by priority and skip current-period local-cap exhaustion.
- request-AC8 -> This task. Proof: `pipeline._fetch_supadata_native_transcript` marks keys exhausted on `SupadataQuotaError` and on `/me` `usedCredits >= maxCredits`, then retries the next key; covered in `tests/test_pipeline.py`.
- request-AC9 -> This task. Proof: `pipeline._fetch_supadata_native_transcript` marks keys invalid on `SupadataAuthError` and continues to the next eligible key.
- request-AC10 -> This task. Proof: all-keys-exhausted and unavailable-native paths raise a controlled captions-step failure pointing to the pasted transcript fallback.
- request-AC11 -> This task. Proof: `TranscriptConfig.provider_order` and `CLAIMLENS_TRANSCRIPT_PROVIDER_ORDER` make provider order explicit, defaulting to `youtube`.
- request-AC12 -> This task. Proof: `TranscriptConfig.supadata_monthly_request_cap` defaults to 100 and controls local current-month eligibility when `/me` data is unavailable.
- request-AC13 -> This task. Proof: Tests cover native request construction, response parsing, quota rotation, exhausted-key skipping, encryption/redaction, Options UI rendering, migration compatibility, and no-auto/no-generate invariants.
- request-AC14 -> This task. Proof: `README.md` documents the exact native Supadata cURL request, key rotation, and fallback behavior.
- request-AC15 -> This task. Proof: Ruff, pytest, compileall, Logics lint, and Logics audit all passed before closeout.

# Validation
- `.venv/bin/ruff check src tests` passed.
- `.venv/bin/pytest` passed with 63 tests.
- `.venv/bin/python -m compileall -q src tests` passed.
- `logics-manager lint --require-status` passed.
- `logics-manager audit --legacy-cutoff-version 1.1.0 --group-by-doc` passed.
- .venv/bin/ruff check src tests passed; .venv/bin/pytest passed with 63 tests; .venv/bin/python -m compileall -q src tests passed; logics-manager lint --require-status passed; logics-manager audit --legacy-cutoff-version 1.1.0 --group-by-doc passed.
- Finish workflow executed on 2026-07-24.
- Linked backlog/request close verification passed.

# Report
- Implemented Supadata native-only transcript acquisition, encrypted multi-key profile storage, quota-aware key rotation, Options UI controls, schema v6, configuration, documentation, and validation coverage.
- Finished on 2026-07-24.
- Linked backlog item(s): `item_049_implement_supadata_native_transcript_client`, `item_050_support_multiple_supadata_keys_per_profile`, `item_051_rotate_supadata_keys_on_quota_exhaustion`, `item_052_expose_supadata_profile_key_management_ui`, `item_053_validate_supadata_native_transcript_delivery`
- Related request(s): `req_007_supadata_native_transcript_key_rotation`

# AI Context
- Summary: Orchestrate Supadata Native Transcript Key Rotation
- Keywords: scaffolded-task, request-chain-scaffold, orchestration
- Use when: Coordinating implementation of a scaffolded request chain.
- Skip when: Working on one isolated sibling slice.

# Links
- Request: `req_007_supadata_native_transcript_key_rotation`
- Product brief(s): `prod_008_claimlens_supadata_native_transcript_key_rotation`
- Architecture decision(s): (none yet)
