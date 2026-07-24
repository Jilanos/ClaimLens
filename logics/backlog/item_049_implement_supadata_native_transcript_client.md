## item_049_implement_supadata_native_transcript_client - Implement Supadata native transcript client
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Medium
> Theme: Transcript provider
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- The deployed app can still fail when server-side YouTube transcript extraction is blocked.
- Supadata offers a transcript endpoint, but ClaimLens needs a strict native-only integration to avoid AI generation.

# Scope
- In:
  - Create a Supadata transcript client around GET https://api.supadata.ai/v1/transcript.
  - Always send mode=native and text=false, with url and optional lang query parameters.
  - Parse content segments into TranscriptResult and TranscriptSegment.
  - Map Supadata errors into controlled transcript provider errors.
  - Add provider-order configuration for transcript acquisition.
  - Document the exact cURL request and native-only invariant.
- Out:
  - Using Supadata auto or generate modes.
  - Using Supadata translation, extract, scrape, file-url transcription, or batch endpoints.
  - Removing youtube-transcript-api support.

# Acceptance criteria
- AC1: Unit tests assert the Supadata request uses x-api-key, mode=native, text=false, url, and optional lang.
- AC2: A Supadata response with offset and duration in milliseconds becomes existing transcript segments in seconds.
- AC3: Non-native modes cannot be selected through config, UI, or client defaults.
- AC4: Captions fail cleanly when Supadata native captions are unavailable.
- AC5: README or deployment docs include the exact native Supadata request.

# AC Traceability
- request-AC1 -> This backlog slice. Proof: AC1: Unit tests assert the Supadata request uses x-api-key, mode=native, text=false, url, and optional lang.
- request-AC2 -> This backlog slice. Proof: AC2: A Supadata response with offset and duration in milliseconds becomes existing transcript segments in seconds.
- request-AC3 -> This backlog slice. Proof: AC3: Non-native modes cannot be selected through config, UI, or client defaults.
- request-AC10 -> This backlog slice. Proof: AC4: Captions fail cleanly when Supadata native captions are unavailable.
- request-AC11 -> This backlog slice. Proof: AC5: README or deployment docs include the exact native Supadata request.
- request-AC13 -> This backlog slice. Proof: AC5: README or deployment docs include the exact native Supadata request.
- request-AC14 -> This backlog slice. Proof: AC5: README or deployment docs include the exact native Supadata request.
- request-AC15 -> This backlog slice. Proof: AC5: README or deployment docs include the exact native Supadata request.
- request-AC6 -> This backlog slice. Evidence needed: Saved Supadata keys are encrypted at rest with the existing deployment secret, never stored in plaintext, never rendered in full, and redacted from exceptions, logs, job payloads, reports, transcripts, and tests.
- request-AC7 -> This backlog slice. Evidence needed: Key selection chooses the first enabled non-exhausted Supadata key by explicit priority, skips keys marked exhausted for the current billing period, and records which key fingerprint was used without storing plaintext.
- request-AC8 -> This backlog slice. Evidence needed: On Supadata 402, 429, or account usage where usedCredits >= maxCredits, ClaimLens marks that key exhausted for the current billing period and retries the same native transcript request with the next eligible key.
- request-AC9 -> This backlog slice. Evidence needed: On Supadata 401, ClaimLens marks the key invalid or test-failed and tries the next eligible key without disabling unrelated providers.
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
- Summary: Implement Supadata native transcript client
- Keywords: scaffolded-backlog, implement supadata native transcript client, implementation-ready
- Use when: Implementing the scaffolded slice for Implement Supadata native transcript client.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.

# Tasks
- `task_008_orchestrate_supadata_native_transcript_key_rotation`

# Notes
- Task `task_008_orchestrate_supadata_native_transcript_key_rotation` was finished via `logics-manager flow finish task` on 2026-07-24.
