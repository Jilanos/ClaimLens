## req_007_supadata_native_transcript_key_rotation - Supadata Native Transcript Key Rotation
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Complexity: High
> Theme: Transcript acquisition
> Reminder: Update status/understanding/confidence and linked backlog/task references when you edit this doc.

# Needs
- Route deployed transcript extraction through Supadata when configured, while preserving the existing local YouTube transcript path as a fallback only when allowed by configuration.
- Add Supadata as a supported encrypted API key provider in authenticated user profiles.
- Allow each authenticated profile to save multiple Supadata API keys with labels, priority, enabled/disabled state, masked display, testing, and deletion.
- Rotate between saved Supadata keys when a key has exhausted its monthly free-tier quota, reaches the account maxCredits/usedCredits limit, or receives a quota response from Supadata.
- Always request Supadata transcripts in native mode so ClaimLens fetches existing subtitles only and never triggers AI generation, auto fallback, translation, extraction, or other higher-credit Supadata features.
- Persist enough usage metadata to avoid repeatedly selecting exhausted keys during the current billing month without storing plaintext keys or leaking keys in logs, jobs, reports, transcripts, or HTML.
- Keep transcript extraction failure clear: if no configured Supadata key has native captions available or quota remaining, stop at the captions step and let the existing pasted transcript fallback continue the run.

# Context
- Supadata requires the x-api-key header and uses https://api.supadata.ai/v1 as the base URL.
- The native transcript request must be GET https://api.supadata.ai/v1/transcript?url=<youtube-url>&lang=<lang>&text=false&mode=native with x-api-key set from the selected profile key.
- Supadata documents transcript mode values native, auto, and generate; ClaimLens must force mode=native and reject config or UI paths that would use auto or generate.
- Supadata account usage is available through GET https://api.supadata.ai/v1/me and returns maxCredits and usedCredits, which can be used to mark a key exhausted for the billing period.
- Supadata returns conventional API status codes including 401 for missing/invalid authentication, 402 for payment required, and 429 when a plan limit is surpassed.
- The current ClaimLens user_api_keys model stores one encrypted key per user/provider, so this request requires a compatible migration to support multiple keys for the supadata provider without weakening existing OpenAI, Semantic Scholar, and NCBI behavior.
- The current transcript boundary lives in src/claimlens/youtube.py and pipeline.extract_required_subtitles stores TranscriptResult values with timestamped segments.
- The current deployed UX already includes an Options page for saved keys and a pasted transcript fallback for VPS-side YouTube blocking.

# Acceptance criteria
- AC1: Supadata is a supported transcript provider with a bounded client that calls GET /v1/transcript using x-api-key and query parameters url, optional lang, text=false, and mode=native.
- AC2: The Supadata client parses synchronous transcript content into the existing TranscriptResult shape, converting offset/duration milliseconds into start/end seconds and preserving language metadata.
- AC3: The Supadata client handles asynchronous job responses defensively if returned, but does not use generate, auto, translation, extract, or file-url transcription modes.
- AC4: Authenticated users can save, list, mask-display, test, enable/disable, reorder, and delete multiple Supadata keys in their profile or Options page.
- AC5: Existing single-key providers OpenAI, Semantic Scholar, and NCBI/PubMed continue to work exactly as before after the schema migration.
- AC6: Saved Supadata keys are encrypted at rest with the existing deployment secret, never stored in plaintext, never rendered in full, and redacted from exceptions, logs, job payloads, reports, transcripts, and tests.
- AC7: Key selection chooses the first enabled non-exhausted Supadata key by explicit priority, skips keys marked exhausted for the current billing period, and records which key fingerprint was used without storing plaintext.
- AC8: On Supadata 402, 429, or account usage where usedCredits >= maxCredits, ClaimLens marks that key exhausted for the current billing period and retries the same native transcript request with the next eligible key.
- AC9: On Supadata 401, ClaimLens marks the key invalid or test-failed and tries the next eligible key without disabling unrelated providers.
- AC10: If every Supadata key is exhausted, invalid, missing, or unable to return native captions, the captions step fails with a user-facing message that explains native Supadata captions were unavailable and points to the pasted transcript fallback.
- AC11: Configuration makes transcript provider order explicit, defaulting to the existing local YouTube transcript extraction unless Supadata is enabled for the deployment or user profile.
- AC12: Supadata free-tier assumptions are configurable, with a default monthly soft cap of 100 requests per key used only as local bookkeeping when /me data is unavailable.
- AC13: Tests cover native request construction, response parsing, quota rotation, exhausted-key skipping, 401/402/429 handling, encryption/redaction, Options UI flows, migration compatibility, and the no-auto/no-generate invariant.
- AC14: Documentation explains the exact Supadata request, the native-only cost-control constraint, how to add multiple keys, how rotation works, and what happens when all keys are exhausted.
- AC15: Validation passes with ruff, pytest, compileall where applicable, logics-manager lint --require-status, and logics-manager audit before closeout.

# Definition of Ready (DoR)
- [x] Problem statement is explicit and user impact is clear.
- [x] Scope boundaries (in/out) are explicit.
- [x] Acceptance criteria are testable.
- [x] Dependencies and known risks are listed.

# Companion docs
- Product brief(s): `prod_008_claimlens_supadata_native_transcript_key_rotation`
- Architecture decision(s): (none yet)

# References
- README.md
- config/claimlens.example.toml
- src/claimlens/youtube.py
- src/claimlens/pipeline.py
- src/claimlens/api_keys.py
- src/claimlens/db.py
- src/claimlens/web.py
- tests/test_youtube.py
- tests/test_pipeline.py
- tests/test_auth_api_keys.py
- https://docs.supadata.ai/api-reference/introduction
- https://docs.supadata.ai/api-reference/endpoint/transcript/transcript
- https://docs.supadata.ai/api-reference/endpoint/account/me

# AI Context
- Summary: Supadata Native Transcript Key Rotation
- Keywords: request-chain-scaffold, supadata native transcript key rotation, development-ready
- Use when: You need to implement or review the scaffolded workflow for Supadata Native Transcript Key Rotation.
- Skip when: The change is unrelated to this scaffolded request chain.

# Backlog
- `item_049_implement_supadata_native_transcript_client`
- `item_050_support_multiple_supadata_keys_per_profile`
- `item_051_rotate_supadata_keys_on_quota_exhaustion`
- `item_052_expose_supadata_profile_key_management_ui`
- `item_053_validate_supadata_native_transcript_delivery`
