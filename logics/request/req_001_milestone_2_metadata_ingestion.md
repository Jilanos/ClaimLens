## req_001_milestone_2_metadata_ingestion - Milestone 2: Metadata Ingestion
> From version: 1.0.0
> Schema version: 1.0
> Status: Draft
> Understanding: 90%
> Confidence: 85%
> Complexity: Medium
> Theme: Ingestion
> Reminder: Update status/understanding/confidence and linked backlog/task references when you edit this doc.

# Needs
- Make `claimlens ingest` fetch recent YouTube video metadata for configured channels.
- Persist channel and video metadata in the existing SQLite database without creating duplicates.
- Make `claimlens candidates` list ingested videos that are ready for later transcript and analysis milestones.
- Keep tests deterministic by mocking API calls and avoiding network dependencies in the automated suite.

# Context
- Milestone 1 created a Python package, CLI shell, configuration loading, SQLite schema, and baseline tests.
- The current `ingest` and `candidates` commands are placeholders.
- The MVP roadmap defines YouTube ingestion as the next implementation step before transcript creation.
- Only `YOUTUBE_API_KEY` should be required for real ingestion; tests must run without external API keys.

# Acceptance criteria
- AC1: Channel definitions can be loaded from a committed example format and from a local configurable channels file.
- AC2: `claimlens ingest` validates that `YOUTUBE_API_KEY` is present before real YouTube API calls.
- AC3: The YouTube ingestion module fetches recent videos for configured channels through a bounded, testable client abstraction.
- AC4: Channel and video metadata are upserted into SQLite idempotently, preserving one record per channel and video ID.
- AC5: Each ingest run records a `pipeline_runs` entry with command, status, timestamps, and useful details.
- AC6: `claimlens candidates` lists ingested videos with enough metadata to manually choose a video for later processing.
- AC7: Ingestion and candidate behavior are covered by tests using mocked YouTube responses and temporary SQLite databases.
- AC8: README documents setup for `YOUTUBE_API_KEY`, channel config, `claimlens ingest`, and `claimlens candidates`.

# Definition of Ready (DoR)
- [x] Problem statement is explicit and user impact is clear.
- [x] Scope boundaries (in/out) are explicit.
- [x] Acceptance criteria are testable.
- [x] Dependencies and known risks are listed.

# Companion docs
- Product brief(s): `prod_002_claimlens_metadata_ingestion`
- Architecture decision(s): (none yet)

# References
- README.md
- ROADMAP.md
- pyproject.toml
- src/claimlens/cli.py
- src/claimlens/config.py
- src/claimlens/db.py
- config/channels.example.toml
- config/claimlens.example.toml

# AI Context
- Summary: Milestone 2: Metadata Ingestion
- Keywords: request-chain-scaffold, milestone 2: metadata ingestion, development-ready
- Use when: You need to implement or review the scaffolded workflow for Milestone 2: Metadata Ingestion.
- Skip when: The change is unrelated to this scaffolded request chain.

# Backlog
- `item_005_load_channel_configuration_for_ingestion`
- `item_006_create_bounded_youtube_metadata_client`
- `item_007_persist_ingested_channels_and_videos`
- `item_008_implement_ingest_and_candidates_cli_commands`
- `item_009_add_ingestion_tests_and_documentation`
