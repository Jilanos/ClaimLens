# ClaimLens

ClaimLens turns selected YouTube videos into sourced, claim-aware briefs.

The MVP focuses on a paid OpenAI-powered workflow for transcription and analysis, while keeping the rest of the stack simple and mostly free: YouTube metadata ingestion, local storage, scientific/source search, and Markdown exports.

## MVP Goal

Build a local pipeline that can:

1. Track a curated list of high-potential YouTube channels.
2. Select relevant videos for processing.
3. Retrieve or create transcripts.
4. Summarize the content.
5. Extract verifiable claims.
6. Check claims against scientific or reliable external sources.
7. Generate a sourced Markdown brief ready for review or blog adaptation.

## Initial Stack

- Python
- SQLite
- YouTube Data API
- OpenAI API for transcription and language analysis
- PubMed / Semantic Scholar / web search for source checks
- Markdown output

## Non-Goals for the MVP

- Automatic publishing to a CMS
- Full multi-user web application
- Perfect fact-check automation
- Large-scale channel monitoring
- Unsupported bypassing of platform restrictions

## Status

Milestone 1 is in progress. See [ROADMAP.md](ROADMAP.md) for the implementation plan.

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
```

Run quality checks:

```bash
ruff check .
pytest
```

## Configuration

ClaimLens reads local configuration from `config/claimlens.example.toml` by default.
Copy or replace it later with a local config file when real API-backed modules are added.

Relevant environment variables:

```bash
CLAIMLENS_DB=data/claimlens.sqlite3
YOUTUBE_API_KEY=
OPENAI_API_KEY=
SEMANTIC_SCHOLAR_API_KEY=
NCBI_API_KEY=
```

`claimlens init-db` does not require API keys.

## MVP Command Surface

```bash
claimlens init-db
claimlens ingest
claimlens candidates
claimlens transcribe <video_id>
claimlens analyze <video_id>
claimlens source-check <video_id>
claimlens brief <video_id>
claimlens run-daily
```

Only `init-db` is implemented in Milestone 1. The other commands are stable placeholders for upcoming milestones.
