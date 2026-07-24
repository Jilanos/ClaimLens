## item_055_remove_supadata_fetch_preflight_latency - Remove Supadata fetch preflight latency
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: High
> Theme: Operator workflow and runtime integration
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
Make Supadata the effective transcript provider for the deployed web app so runs stop silently falling back to the classic `youtube_transcript_api` path, which is slow and gets rejected/rate-limited from the VPS.
Set the deployed Compose environment to `CLAIMLENS_TRANSCRIPT_PROVIDER_ORDER=supadata,youtube`; keep the local/example TOML default as `youtube` so Supadata remains opt-in outside deployment.
Remove the accidental per-request latency in the Supadata path so a successful native fetch is not preceded by an unconditional, high-timeout `/me` account call on every attempt.
Replace the hardcoded 30s Supadata request timeout with a configurable 10s default so a slow or unreachable key cannot stall a run for minutes across sequential keys.
Keep the native-only invariant and multi-key rotation from req_007 fully intact; this request only fixes provider selection and latency, not the client contract.

# Scope
- In:
  - one coherent delivery slice from the source request
- Out:
  - unrelated sibling slices that should stay in separate backlog items instead of widening this doc

# Acceptance criteria
- AC4: The pipeline never calls `/me` before `GET /transcript`. It skips keys already marked exhausted in local billing-period bookkeeping; it treats transcript 402/429 responses as authoritative exhaustion and rotates to the next eligible key. `/me` may remain available only for explicit key-testing or non-critical reconciliation flows.
- AC5: `TranscriptConfig` exposes `supadata_timeout_seconds`, defaulting to 10, with a `CLAIMLENS_SUPADATA_TIMEOUT_SECONDS` override. This value is passed to every Supadata client request and documented in the example configuration and deployment guide.
- AC6: The native-only invariant (`text=false`, `mode=native`, no auto/generate/translate) and the multi-key rotation/quota behavior from req_007 are unchanged and still covered by tests.

# AC Traceability
- request-AC4 -> This backlog slice. Proof: AC4: The pipeline never calls `/me` before `GET /transcript`. It skips keys already marked exhausted in local billing-period bookkeeping; it treats transcript 402/429 responses as authoritative exhaustion and rotates to the next eligible key. `/me` may remain available only for explicit key-testing or non-critical reconciliation flows.
- request-AC5 -> This backlog slice. Proof: AC5: `TranscriptConfig` exposes `supadata_timeout_seconds`, defaulting to 10, with a `CLAIMLENS_SUPADATA_TIMEOUT_SECONDS` override. This value is passed to every Supadata client request and documented in the example configuration and deployment guide.
- request-AC6 -> This backlog slice. Proof: AC6: The native-only invariant (`text=false`, `mode=native`, no auto/generate/translate) and the multi-key rotation/quota behavior from req_007 are unchanged and still covered by tests.
- request-AC1 -> This backlog slice. Evidence needed: `docs/deployment-paulmondou-infra.md` sets `CLAIMLENS_TRANSCRIPT_PROVIDER_ORDER=supadata,youtube` in the ClaimLens Compose service; the deployed web entrypoint consumes that environment variable. `config/claimlens.example.toml` remains local-first with `youtube` as its default.
- request-AC2 -> This backlog slice. Evidence needed: With a valid enabled Supadata key, a run fetches captions via `supadata-native` without ever invoking the classic `youtube_transcript_api` path first.
- request-AC3 -> This backlog slice. Evidence needed: `youtube` remains available strictly as an explicit, configurable secondary fallback and is only attempted after all eligible Supadata keys fail to return native captions.
- request-AC7 -> This backlog slice. Evidence needed: Tests cover: provider order resolves `supadata,youtube` from the Compose/deployment environment; the classic YouTube path is not called when Supadata succeeds; fallback to YouTube still works when Supadata is unconfigured or all keys fail; no `/me` call precedes a successful native fetch; and the configured timeout reaches the client.
- request-AC8 -> This backlog slice. Evidence needed: Documentation distinguishes the local `youtube` default from the deployed `supadata,youtube` setting, explains the fallback sequence, and documents `CLAIMLENS_SUPADATA_TIMEOUT_SECONDS` with its 10s default.
- request-AC9 -> This backlog slice. Evidence needed: Validation passes with ruff, pytest, and `logics-manager lint --require-status` and `logics-manager audit` before closeout.

# Decision framing
- Product framing: Not needed
- Product signals: (none detected)
- Product follow-up: No product brief follow-up is expected based on current signals.
- Architecture framing: Not needed
- Architecture signals: (none detected)
- Architecture follow-up: No architecture decision follow-up is expected based on current signals.

# Links
- Product brief(s): `prod_010_remove_supadata_fetch_preflight_latency`
- Architecture decision(s): (none yet)
- Request: `req_008_supadata_first_provider_order_fix`
- Primary task(s): `task_009_orchestrate_supadata_first_deployment_provider_fix`

# AI Context
- Summary: Remove Supadata fetch preflight latency
- Keywords: backlog-groom, request, remove supadata fetch preflight latency, bounded slice
- Use when: Use when implementing or reviewing the delivery slice for Remove Supadata fetch preflight latency.
- Skip when: Skip when the change is unrelated to this delivery slice or its linked request.

# Priority
- Priority: Medium
- Rationale: Default until groomed.

# Notes
- Hybrid rationale: Derived from request `req_008_supadata_first_provider_order_fix` and kept bounded to one coherent delivery slice.
- Source file: `logics/request/req_008_supadata_first_provider_order_fix.md`.
- Generated locally by logics-manager.
- Task `task_009_orchestrate_supadata_first_deployment_provider_fix` was finished via `logics-manager flow finish task` on 2026-07-24.

# Tasks
- `task_009_orchestrate_supadata_first_deployment_provider_fix`
