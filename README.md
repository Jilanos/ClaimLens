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
claimlens transcribe https://www.youtube.com/watch?v=W7DVR9TlpOs --database data/claimlens.sqlite3
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

`OPENAI_API_KEY` is required for the planned LLM analysis step. It should be supplied at run start
through environment/config, prompt, or the local HTML UI and must not be persisted in generated
outputs.

Optional future source verification keys:

```bash
SEMANTIC_SCHOLAR_API_KEY=
NCBI_API_KEY=
```

## Current Implementation

Implemented:

- Python package and CLI shell.
- Config loading.
- SQLite schema initialization.
- Subtitle extraction for a YouTube video ID, video URL, or channel URL.
- Transcript and segment persistence in SQLite.

Still to implement for the refined MVP:

- Single-video run state.
- Mandatory subtitle failure handling as a first-class pipeline state.
- Cleaned transcript artifact.
- OpenAI analysis.
- Direct Markdown brief generation.
- Local HTML process page.

## SQLite Schema

Schema version 1 creates the base tables for pipeline state and later analysis:

- `channels`
- `videos`
- `pipeline_runs`
- `transcripts`
- `transcript_segments`
- `summaries`
- `claims`
- `sources`
- `claim_sources`

Before introducing schema version 2, any additive or destructive production schema change must
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
