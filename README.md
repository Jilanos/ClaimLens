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

Project initialized. See [ROADMAP.md](ROADMAP.md) for the implementation plan.
