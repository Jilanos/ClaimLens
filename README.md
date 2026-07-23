# ClaimLens

ClaimLens turns one YouTube video URL into a local, reviewable brief.

The refined MVP is local-first:

1. Enter one YouTube video URL.
2. Extract existing YouTube subtitles.
3. Stop with a clear failure if subtitles are unavailable.
4. Clean the transcript for LLM input.
5. Use OpenAI to generate a structured analysis.
6. Generate a Markdown brief.
7. Inspect and launch steps from a local HTML process page.

Channel monitoring, candidate scoring, source retrieval, and evidence verdicts are no longer base
MVP requirements. Advanced source verification is planned as an optional mode after the base one-
video workflow is reliable.

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
the current working directory. Run the CLI from the repository root for the default local workflow,
or pass an explicit config path in code when embedding the package.

Relevant environment variables:

```bash
CLAIMLENS_DB=data/claimlens.sqlite3
CLAIMLENS_OUTPUTS=outputs
CLAIMLENS_TRANSCRIPTS=outputs/transcripts
CLAIMLENS_BRIEFS=outputs/briefs
CLAIMLENS_HOST=127.0.0.1
CLAIMLENS_PORT=8765
OPENAI_API_KEY=
```

`OPENAI_API_KEY` is required for the LLM analysis step. It can be supplied through the environment,
`--openai-api-key`, or the local HTML UI and is not persisted in SQLite, generated transcripts, or
generated briefs.

Optional future source verification keys:

```bash
SEMANTIC_SCHOLAR_API_KEY=
NCBI_API_KEY=
```

Advanced source verification is disabled by default:

```toml
[sources]
advanced_source_verification = false
```

## Current Implementation

Implemented:

- Python package and CLI shell.
- Config loading.
- SQLite schema initialization.
- Single-video run state.
- URL validation for one YouTube video URL.
- Mandatory subtitle extraction with persisted failure causes.
- Transcript and segment persistence in SQLite.
- Cleaned transcript artifacts.
- Mockable OpenAI analysis boundary and structured analysis storage.
- Direct Markdown brief generation labeled as not advanced-source-verified.
- Local HTML process page with step statuses, failure details, outputs, and next-step controls.

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

## SQLite Schema

Schema version 1 creates the base tables for pipeline state and later analysis:

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
- `brief_artifacts`

Before introducing schema version 3, any additive or destructive production schema change must
include a tested migration path.

## Refined Command Surface

Target MVP commands:

```bash
claimlens init-db
claimlens run-video <youtube_video_url>
claimlens transcribe <youtube_video_url>
claimlens analyze <video_id>
claimlens brief <video_id>
claimlens serve
```

Existing compatibility placeholders such as `ingest`, `candidates`, and `run-daily` may remain
temporarily, but they are not part of the refined base MVP.
