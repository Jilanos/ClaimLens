## req_008_supadata_first_provider_order_fix - Enable Supadata-first transcript provider order in deployment
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 95
> Confidence: 90
> Complexity: Low
> Theme: Transcript acquisition
> Reminder: Update status/understanding/confidence and linked backlog/task references when you edit this doc.

# Needs
- Make Supadata the effective transcript provider for the deployed web app so runs stop silently falling back to the classic `youtube_transcript_api` path, which is slow and gets rejected/rate-limited from the VPS.
- Set the deployed Compose environment to `CLAIMLENS_TRANSCRIPT_PROVIDER_ORDER=supadata,youtube`; keep the local/example TOML default as `youtube` so Supadata remains opt-in outside deployment.
- Remove the accidental per-request latency in the Supadata path so a successful native fetch is not preceded by an unconditional, high-timeout `/me` account call on every attempt.
- Replace the hardcoded 30s Supadata request timeout with a configurable 10s default so a slow or unreachable key cannot stall a run for minutes across sequential keys.
- Keep the native-only invariant and multi-key rotation from req_007 fully intact; this request only fixes provider selection and latency, not the client contract.

# Context
- Provider selection is purely config-driven in `_fetch_configured_transcript` (`src/claimlens/pipeline.py:186-208`); there is no automatic error-based switch from YouTube to Supadata.
- `transcripts.provider_order` defaults to `("youtube",)` in `src/claimlens/config.py:158-160` (`transcripts_config.get("provider_order", "youtube")`).
- The only config file on disk is `config/claimlens.example.toml`, which correctly keeps the local default `provider_order = ["youtube"]`; the Compose deployment example does not set `CLAIMLENS_TRANSCRIPT_PROVIDER_ORDER`. Result: deployed runs use the local default and Supadata is never reached.
- Provider order is sequential and each step blocks: with `["youtube", "supadata"]` the classic path is attempted first and burns its timeouts / gets rejected before Supadata is ever tried (`pipeline.py:188-194`).
- Inside the Supadata path, each candidate key triggers `client.account_info()` → `GET /me` before `client.fetch_native_transcript()` → `GET /transcript` (`pipeline.py:239` then `:267`), each with a 30s hardcoded timeout (`src/claimlens/youtube.py:75`, applied at `:159`). Worst case is about 60s per key, sequential across keys.
- req_007 already delivered the native-only Supadata client, multi-key storage, rotation, and quota handling; this request depends on that work and must not regress it.

# Acceptance criteria
- AC1: `docs/deployment-paulmondou-infra.md` sets `CLAIMLENS_TRANSCRIPT_PROVIDER_ORDER=supadata,youtube` in the ClaimLens Compose service; the deployed web entrypoint consumes that environment variable. `config/claimlens.example.toml` remains local-first with `youtube` as its default.
- AC2: With a valid enabled Supadata key, a run fetches captions via `supadata-native` without ever invoking the classic `youtube_transcript_api` path first.
- AC3: `youtube` remains available strictly as an explicit, configurable secondary fallback and is only attempted after all eligible Supadata keys fail to return native captions.
- AC4: The pipeline never calls `/me` before `GET /transcript`. It skips keys already marked exhausted in local billing-period bookkeeping; it treats transcript 402/429 responses as authoritative exhaustion and rotates to the next eligible key. `/me` may remain available only for explicit key-testing or non-critical reconciliation flows.
- AC5: `TranscriptConfig` exposes `supadata_timeout_seconds`, defaulting to 10, with a `CLAIMLENS_SUPADATA_TIMEOUT_SECONDS` override. This value is passed to every Supadata client request and documented in the example configuration and deployment guide.
- AC6: The native-only invariant (`text=false`, `mode=native`, no auto/generate/translate) and the multi-key rotation/quota behavior from req_007 are unchanged and still covered by tests.
- AC7: Tests cover: provider order resolves `supadata,youtube` from the Compose/deployment environment; the classic YouTube path is not called when Supadata succeeds; fallback to YouTube still works when Supadata is unconfigured or all keys fail; no `/me` call precedes a successful native fetch; and the configured timeout reaches the client.
- AC8: Documentation distinguishes the local `youtube` default from the deployed `supadata,youtube` setting, explains the fallback sequence, and documents `CLAIMLENS_SUPADATA_TIMEOUT_SECONDS` with its 10s default.
- AC9: Validation passes with ruff, pytest, and `logics-manager lint --require-status` and `logics-manager audit` before closeout.

# Definition of Ready (DoR)
- [x] Problem statement is explicit and user impact is clear.
- [x] Scope boundaries (in/out) are explicit.
- [x] Acceptance criteria are testable.
- [x] Dependencies and known risks are listed.

# Companion docs
- Product brief(s): (none yet)
- Architecture decision(s): (none yet)

# References
- config/claimlens.example.toml
- src/claimlens/config.py
- src/claimlens/pipeline.py
- src/claimlens/youtube.py
- src/claimlens/web.py
- README.md
- tests/test_pipeline.py
- tests/test_youtube.py
- `logics/request/req_007_supadata_native_transcript_key_rotation.md`

# AI Context
- Summary: Fix transcript provider selection so deployment uses Supadata first instead of silently falling back to the slow, blocked classic YouTube path, and trim Supadata-path latency.
- Keywords: supadata, provider_order, transcript, youtube fallback, latency, /me call, timeout, deployment config
- Use when: Runs are slow or fail at the captions step and appear to be using the classic YouTube API despite Supadata being available.
- Skip when: The change concerns the Supadata client contract itself or unrelated pipeline steps.

# Scope (out)
- No new Supadata modes (auto/generate/translate) — native-only stays enforced.
- No changes to the multi-key storage/encryption model from req_007.
- No changes to the pasted-transcript manual fallback behavior.

# Risks
- Enabling Supadata-first for guests: the Supadata path requires `user_id`, so unauthenticated/CLI runs must still degrade cleanly to YouTube or the pasted fallback.
- Removing the `/me` gate relies on local billing-period bookkeeping. A stale record can cost one native request; 402/429 remain authoritative and must immediately mark the key exhausted before rotation.

# Backlog
- none
- `item_054_configure_supadata_first_deployment`
- `item_055_remove_supadata_fetch_preflight_latency`
- `item_056_validate_supadata_first_fallback_delivery`
