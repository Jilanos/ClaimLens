# ClaimLens

ClaimLens turns one YouTube video URL into a local, reviewable brief.

The refined MVP is local-first:

1. Enter one YouTube video URL.
2. Extract existing YouTube subtitles.
3. Stop with a clear failure if subtitles are unavailable.
4. Clean the transcript for LLM input.
5. Use OpenAI to generate a structured analysis.
6. Generate a Markdown brief.
7. Optionally verify notable claims against PubMed and Semantic Scholar.
8. Inspect and launch steps from a local HTML process page with guarded POST actions, live async job
   status, and report viewing/download.
9. Optionally log in to reuse encrypted per-user API keys and manage them from Options.

Channel monitoring and candidate scoring are no longer base MVP requirements. Advanced source
verification is optional and disabled by default; when launched, it checks stored notable claims
against PubMed and Semantic Scholar candidates and renders a source-verified brief.

## Local Development

Create a virtual environment and install the project:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

Run the CLI:

```bash
claimlens --help
claimlens init-db
claimlens run-video https://www.youtube.com/watch?v=W7DVR9TlpOs --database data/claimlens.sqlite3
```

Run quality checks:

```bash
ruff check .
pytest
```

## Configuration

ClaimLens reads local configuration from `config/claimlens.example.toml` by default, resolved from
the current working directory. Run the CLI from the repository root for the default local workflow.
For deployed execution, set `CLAIMLENS_CONFIG` or pass `--config`; relative paths inside an
explicit config file resolve from that file's directory.

Relevant environment variables:

```bash
CLAIMLENS_DB=data/claimlens.sqlite3
CLAIMLENS_OUTPUTS=outputs
CLAIMLENS_TRANSCRIPTS=outputs/transcripts
CLAIMLENS_BRIEFS=outputs/briefs
CLAIMLENS_CONFIG=config/claimlens.example.toml
CLAIMLENS_HOST=127.0.0.1
CLAIMLENS_PORT=8765
CLAIMLENS_KAPSULE_DB=
CLAIMLENS_KEY_ENCRYPTION_SECRET=
CLAIMLENS_SECURE_COOKIES=false
CLAIMLENS_REGISTRATION_ENABLED=false
CLAIMLENS_ALLOW_SERVER_API_KEY_FALLBACK=true
CLAIMLENS_TRANSCRIPT_PROVIDER_ORDER=youtube
CLAIMLENS_SUPADATA_LANGUAGE=en
CLAIMLENS_SUPADATA_TIMEOUT_SECONDS=10
OPENAI_API_KEY=
SEMANTIC_SCHOLAR_API_KEY=
NCBI_API_KEY=
```

`OPENAI_API_KEY` is required for the LLM analysis step. It can be supplied through the environment,
`--openai-api-key`, or the local HTML UI and is not persisted in SQLite, generated transcripts, or
generated briefs.

Authenticated web users can save OpenAI, Semantic Scholar, and NCBI/PubMed keys from the Options
page. Saved keys are encrypted in SQLite with `CLAIMLENS_KEY_ENCRYPTION_SECRET`; keep that secret
outside Git and back it up separately. Guest users can still enter keys per process, and those keys
are used only for the submitted job/action. On the Process page, signed-in users with a saved key
do not see a redundant per-run key field; guests and users without that provider key can still enter
one for the submitted action.

Authenticated users can also save multiple Supadata keys from Options. Supadata transcript fetching
is opt-in through configuration. Local runs keep the classic YouTube path by default; the deployed
Compose service sets `CLAIMLENS_TRANSCRIPT_PROVIDER_ORDER=supadata,youtube` so native Supadata
captions are tried first and YouTube is used only as an explicit fallback:

```toml
[transcripts]
provider_order = ["supadata", "youtube"]
supadata_monthly_request_cap = 100
supadata_language = "en"
supadata_timeout_seconds = 10
```

ClaimLens always calls Supadata in native subtitle mode:

```bash
curl --request GET \
  --url 'https://api.supadata.ai/v1/transcript?url=https%3A%2F%2Fwww.youtube.com%2Fwatch%3Fv%3DVIDEO_ID&lang=en&text=false&mode=native' \
  --header 'x-api-key: <SUPADATA_API_KEY>'
```

The application does not expose or call Supadata `auto`, `generate`, translation, extract, or file
transcription modes. Saved Supadata keys are tried by priority; keys already exhausted in local
bookkeeping are skipped, and transcript quota responses mark a key exhausted until the next billing
month. The transcript request does not call `/me` first, so successful native captions avoid the
account preflight latency. `CLAIMLENS_SUPADATA_TIMEOUT_SECONDS` overrides the 10-second request
timeout. When all native Supadata keys are exhausted, invalid, or missing, the configured YouTube
fallback is attempted; if no provider succeeds, the pasted transcript fallback remains available.

When `CLAIMLENS_KAPSULE_DB` points to a readable Kapsule SQLite database, ClaimLens also accepts
existing Kapsule email/password credentials. The Kapsule database is read-only from ClaimLens; the
first successful Kapsule login provisions a local ClaimLens user row so ClaimLens-owned API keys,
runs, and sessions remain isolated in the ClaimLens database.

Advanced source verification is disabled by default:

```toml
[pipeline]
source_verification_max_results = 5
source_verification_timeout_seconds = 20
analysis_max_chars = 60000
report_language = "en"

[web]
max_request_bytes = 16384
rate_limit_actions = 12
rate_limit_window_seconds = 300

[sources]
advanced_source_verification = false
```

The Process page polls active job state every two seconds through a run-scoped JSON endpoint and
stops when the job reaches a terminal state. It displays semantic status and messages rather than a
numeric percentage, because external provider calls do not expose reliable intermediate progress.

The source verification keys are optional for local tests and some API usage, but should be supplied
for real PubMed/Semantic Scholar smoke testing. They are runtime/config inputs only and are not
persisted in SQLite, generated transcripts, generated briefs, or the local HTML output.
PubMed and Semantic Scholar can run without keys; saved or environment keys only improve quota and
reliability. Verification reports list each adapter outcome, including no candidates, timeouts, and
rate limits. A run with warnings is not presented as fully source-verified; a Semantic Scholar HTTP
429 is retried once with a bounded delay and then shown with remediation guidance.

## Current Implementation

Implemented:

- Python package and CLI shell.
- Config loading.
- SQLite schema initialization.
- Single-video run state.
- URL validation for one YouTube video URL.
- Mandatory subtitle extraction with persisted failure causes.
- Transcript and segment persistence in SQLite.
- Cleaned transcript artifacts reflowed into readable paragraphs while raw timestamped segments remain
  available.
- Mockable OpenAI analysis boundary and structured analysis storage.
- Direct Markdown brief generation labeled as not advanced-source-verified.
- Optional PubMed/Semantic Scholar source verification for stored notable claims.
- Non-binary claim verdicts: supported, contradicted, mixed, unclear, and not_checked.
- Source-verified Markdown brief generation with supporting/contradicting evidence snippets.
- Local HTML process page with CSRF-protected actions, bounded request bodies, live job state,
  semantic status messages, failure details, transcript preview, source links, report viewing,
  report download, and next-step controls.
- Login/logout, secure session storage, top navigation, and an Options page for encrypted per-user
  API key management.
- Optional Kapsule account login bridge for shared paulmondou.fr credentials.
- Pasted transcript fallback for VPS/IP-blocked YouTube caption extraction.
- SQLite WAL and `busy_timeout` pragmas for local concurrent web access.
- Conservative source verification: adapter errors are logged and source verdicts no longer rely
  on title/snippet keyword polarity alone.

Manual smoke test:

1. Successful path with a real captioned video:

```bash
export OPENAI_API_KEY=...
claimlens init-db --database data/claimlens.sqlite3
claimlens run-video "https://www.youtube.com/watch?v=W7DVR9TlpOs" --database data/claimlens.sqlite3
```

2. Expected stopped path with a video that has no YouTube captions:

```bash
claimlens run-video "https://www.youtube.com/watch?v=<no-caption-video-id>" --database data/claimlens.sqlite3
```

The second path should stop at the captions step with a persisted message explaining that subtitles
are unavailable and the base MVP does not use audio fallback.

3. Optional source verification after a successful analysis:

```bash
export SEMANTIC_SCHOLAR_API_KEY=...
export NCBI_API_KEY=...
claimlens verify-sources "W7DVR9TlpOs" --database data/claimlens.sqlite3
claimlens brief "W7DVR9TlpOs" --verified --database data/claimlens.sqlite3
```

This writes `outputs/briefs/<video_id>.verified.md`. The verified brief includes a human-review
disclaimer because PubMed/Semantic Scholar snippets are review aids, not final medical advice or
scientific authority.

4. HTML workflow:

```bash
claimlens serve
```

Open `http://127.0.0.1:8765`, load a run, and launch `source verification` after analysis exists.
The page shows job status, verification status, failure details, source counts, transcript preview,
and links to view or download the generated Markdown report.

For a private local login test:

```bash
export CLAIMLENS_KEY_ENCRYPTION_SECRET="$(openssl rand -hex 32)"
export CLAIMLENS_SECURE_COOKIES=false
claimlens serve
```

Open `/login`. If no user exists, the create-account form bootstraps the first account even when
registration is otherwise closed. After login, use `/options` to save, test, or delete API keys.

Online-readiness smoke checks:

- Oversized or stale form submissions should be rejected with controlled messages.
- Repeated costly actions should be rejected while the same action is queued or running.
- Report links must only serve files from the configured briefs directory.
- Channel page scraping is disabled in the exposed CLI workflow; use one direct video URL.
- If YouTube blocks transcript extraction, paste transcript text into the fallback form and continue
  with cleanup, analysis, brief, and verification.

Deployment notes:

- ClaimLens now supports BYO keys for guests and encrypted saved keys for authenticated users.
  Keep `CLAIMLENS_ALLOW_SERVER_API_KEY_FALLBACK=false` if you do not want any server-owned key use.
- HTTPS still belongs at Caddy/reverse-proxy level. Do not publish the ClaimLens container port
  directly. The deployable app shape is documented in `docs/deployment-paulmondou-infra.md`.

## SQLite Schema

Schema version 6 creates and migrates the local tables for pipeline state, analysis, verification,
brief artifacts, async jobs, web users, sessions, encrypted API keys, and Supadata key pools:

- `channels`
- `videos`
- `pipeline_runs`
- `run_steps`
- `transcripts`
- `transcript_segments`
- `cleaned_transcripts`
- `summaries`
- `claims`
- `sources`
- `claim_sources`
- `verification_runs`
- `evidence_snippets`
- `brief_artifacts`
- `jobs`
- `users`
- `sessions`
- `user_api_keys`
- `supadata_api_keys`

Before introducing the next schema version, any additive or destructive production schema change
must include a tested migration path against an older schema/database fixture.

## Refined Command Surface

Target MVP commands:

```bash
claimlens init-db
claimlens run-video <youtube_video_url>
claimlens transcribe <youtube_video_url>
claimlens analyze <video_id>
claimlens brief <video_id>
claimlens verify-sources <video_id>
claimlens brief <video_id> --verified
claimlens serve
```

Existing compatibility placeholders such as `ingest`, `candidates`, and `run-daily` may remain
temporarily, but they are not part of the refined base MVP.
