## item_005_load_channel_configuration_for_ingestion - Load channel configuration for ingestion
> From version: 1.0.0
> Schema version: 1.0
> Status: Obsolete
> Understanding: 90%
> Confidence: 85%
> Progress: 0%
> Complexity: Low
> Theme: Ingestion
> Non-semantic edit: withdrawn by logics-manager; superseded by the single-video MVP chain.
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- Ingestion needs a stable way to know which YouTube channels are in scope.
- The existing example channel config is not yet wired into runtime behavior.

# Scope
- In:
  - Define the channel config contract.
  - Load channel IDs, names, priorities, and keywords from TOML.
  - Allow a configurable channels file path.
  - Document the expected file format.
- Out:
  - Remote channel management.
  - A database-backed channel administration UI.
  - Advanced topic taxonomy configuration.

# Acceptance criteria
- AC1: Channel config loading returns typed channel records.
- AC2: The loader works with `config/channels.example.toml`.
- AC3: Missing optional fields get safe defaults.
- AC4: README documents how to provide a local channels file.

# AC Traceability
- request-AC1 -> This backlog slice. Proof: AC1: Channel config loading returns typed channel records.
- request-AC8 -> This backlog slice. Proof: AC2: The loader works with `config/channels.example.toml`.
- request-AC3 -> This backlog slice. Evidence needed: The YouTube ingestion module fetches recent videos for configured channels through a bounded, testable client abstraction.
- request-AC4 -> This backlog slice. Evidence needed: Channel and video metadata are upserted into SQLite idempotently, preserving one record per channel and video ID.
- request-AC5 -> This backlog slice. Evidence needed: Each ingest run records a `pipeline_runs` entry with command, status, timestamps, and useful details.
- request-AC6 -> This backlog slice. Evidence needed: `claimlens candidates` lists ingested videos with enough metadata to manually choose a video for later processing.
- request-AC7 -> This backlog slice. Evidence needed: Ingestion and candidate behavior are covered by tests using mocked YouTube responses and temporary SQLite databases.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_002_claimlens_metadata_ingestion`
- Architecture decision(s): (none yet)
- Request: `req_001_milestone_2_metadata_ingestion`
- Primary task(s): `task_002_orchestrate_milestone_2_metadata_ingestion`
- Superseded by: `item_014_implement_single_video_run_model_and_url_input`

# AI Context
- Summary: Load channel configuration for ingestion
- Keywords: scaffolded-backlog, load channel configuration for ingestion, implementation-ready
- Use when: Implementing the scaffolded slice for Load channel configuration for ingestion.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.
