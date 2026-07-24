## task_007_orchestrate_deployable_web_auth_and_api_key_management - Orchestrate Deployable Web Auth And API Key Management
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
- [x] 1. Confirm paulmondou-infra deployment constraints and keep ClaimLens as a separate deployable app/service.
- [x] 2. Design schema v5 for users, sessions, encrypted API keys, ownership, and transcript fallback.
- [x] 3. Implement authentication and secure session handling before adding saved secret storage.
- [x] 4. Implement encrypted user API key storage with redaction and provider-specific key resolution.
- [x] 5. Update process execution so guest keys are transient and authenticated saved keys are reused safely.
- [x] 6. Add top navigation, login/logout pages, and authenticated Options page.
- [x] 7. Add transcript paste/upload fallback for VPS-side YouTube blocking.
- [x] 8. Package ClaimLens for container deployment and document paulmondou-infra Compose/Caddy changes.
- [x] 9. Update docs, deployment runbook, and manual smoke tests.
- [x] 10. Validate with deterministic tests, ruff, compileall, logics lint, and logics audit before closeout.
- [x] 11. ADR 009 checkpoint: update affected Logics docs during each meaningful wave and leave the repo commit-ready; commit creation remains under operator control.
- [x] ADR 009 checkpoint: update affected Logics docs during each meaningful wave and leave the repo commit-ready.
- [x] Keep commit creation under operator control; do not force one commit per micro-step.
- [x] GATE: do not close until lint, audit, and scaffold validation pass.

# Backlog
- `item_041_package_claimlens_for_container_deployment`
- `item_042_specify_paulmondou_infra_integration`
- `item_043_implement_web_users_and_sessions`
- `item_044_encrypt_and_manage_user_api_keys`
- `item_045_add_guest_and_authenticated_process_key_resolution`
- `item_046_build_login_navigation_and_options_ui`
- `item_047_add_transcript_fallback_for_vps_blocked_youtube`
- `item_048_version_schema_and_validate_deployable_closeout`

# Definition of Done (DoD)
- [x] Generated request, product, backlog, and task docs are present.
- [x] Context-pack handoff is available when requested.
- [x] Validation passes.
- [x] Meaningful waves followed ADR 009: affected docs updated and the repo left commit-ready without automatic commits.

# AC Traceability
- request-AC1 -> This task. Proof: `Dockerfile`, `.dockerignore`, `/health`, and `docs/deployment-paulmondou-infra.md` define the deployable container runtime, healthcheck, persistent data paths, and production env variables.
- request-AC2 -> This task. Proof: `docs/deployment-paulmondou-infra.md` documents the ClaimLens Compose service, `CLAIMLENS_DOMAIN`, `CLAIMLENS_APP_DIR`, Caddy `reverse_proxy`, volume, env, deploy command, and backup secret expectations.
- request-AC3 -> This task. Proof: `src/claimlens/auth.py`, schema v5 `users`/`sessions`, and `web.py` implement registration/bootstrap, login, logout, password hashing, session cookies, and CSRF-compatible session state.
- request-AC4 -> This task. Proof: `web.py:_nav` renders top navigation with guest login state and authenticated Options/Logout state.
- request-AC5 -> This task. Proof: `render_options_page` and POST actions `save_api_key`, `test_api_key`, and `delete_api_key` manage OpenAI, Semantic Scholar, and NCBI/PubMed keys.
- request-AC6 -> This task. Proof: `src/claimlens/secrets.py` encrypts and authenticates saved key material with `CLAIMLENS_KEY_ENCRYPTION_SECRET`; stored DB values are encrypted/masked and tests assert plaintext is absent.
- request-AC7 -> This task. Proof: guest process forms still accept per-action keys, `KeyContext.request_keys` resolves them transiently, and jobs do not persist form key values.
- request-AC8 -> This task. Proof: `src/claimlens/api_keys.py:resolve_api_key` implements request key, saved user key, optional server fallback, and anonymous/no-key resolution order with tests.
- request-AC9 -> This task. Proof: source verification still instantiates PubMed/Semantic Scholar adapters with `None` keys when no key is available.
- request-AC10 -> This task. Proof: `pipeline_runs.user_id`, `pipeline_runs.guest_token`, visible-run queries, report path resolution, and tests enforce owner/guest scoping.
- request-AC11 -> This task. Proof: `pipeline.add_manual_transcript` and the web fallback textarea let users paste transcript text when YouTube captions are blocked; tests cover continued cleanup.
- request-AC12 -> This task. Proof: schema version 5 adds users, sessions, user_api_keys, run ownership, and transcript submission metadata; tests verify schema v5 tables.
- request-AC13 -> This task. Proof: README and `docs/deployment-paulmondou-infra.md` cover HTTPS behind Caddy, non-public container port, secure cookies, secret generation, and backup/restore warnings.
- request-AC14 -> This task. Proof: tests cover password hashing, session token hashing, encrypted key round trip, key redaction/masking, resolution order, anonymous adapter behavior, report access control, options rendering, and transcript fallback.
- request-AC15 -> This task. Proof: `.venv/bin/ruff check .`, `.venv/bin/pytest`, `.venv/bin/python -m compileall -q src tests`, `logics-manager lint --require-status`, and `logics-manager audit` passed during closeout.

# Validation
- `.venv/bin/ruff check .` passed.
- `.venv/bin/pytest` passed with 51 tests.
- `.venv/bin/python -m compileall -q src tests` passed.
- `logics-manager lint --require-status` passed.
- `logics-manager audit` passed before closeout with only deferred-proof warnings while the task was not yet Done.
- .venv/bin/ruff check . passed; .venv/bin/pytest passed with 51 tests; .venv/bin/python -m compileall -q src tests passed; logics-manager lint --require-status passed; logics-manager audit passed with only pre-closeout deferred-proof warnings.
- Finish workflow executed on 2026-07-24.
- Linked backlog/request close verification passed.

# Report
- Implemented deployable web auth, encrypted per-user API key management, guest key behavior, transcript paste fallback, and paulmondou-infra deployment preparation.
- Finished on 2026-07-24.
- Linked backlog item(s): `item_041_package_claimlens_for_container_deployment`, `item_042_specify_paulmondou_infra_integration`, `item_043_implement_web_users_and_sessions`, `item_044_encrypt_and_manage_user_api_keys`, `item_045_add_guest_and_authenticated_process_key_resolution`, `item_046_build_login_navigation_and_options_ui`, `item_047_add_transcript_fallback_for_vps_blocked_youtube`, `item_048_version_schema_and_validate_deployable_closeout`
- Related request(s): `req_006_deployable_web_auth_and_api_key_management`

# AI Context
- Summary: Orchestrate Deployable Web Auth And API Key Management
- Keywords: scaffolded-task, request-chain-scaffold, orchestration
- Use when: Coordinating implementation of a scaffolded request chain.
- Skip when: Working on one isolated sibling slice.

# Links
- Request: `req_006_deployable_web_auth_and_api_key_management`
- Product brief(s): `prod_007_claimlens_deployable_web_auth_and_api_key_management`
- Architecture decision(s): (none yet)
