## task_002_orchestrate_milestone_2_metadata_ingestion - Orchestrate Milestone 2 Metadata Ingestion
> From version: 1.0.0
> Schema version: 1.0
> Status: Obsolete
> Understanding: 90%
> Confidence: 85%
> Progress: 0%
> Complexity: Medium
> Theme: Implementation delivery
> Non-semantic edit: withdrawn by logics-manager; superseded by the single-video MVP chain.
> Reminder: Update status/understanding/confidence/progress and linked request/backlog references when you edit this doc.

# Context
- Orchestrate the scaffolded request chain and keep sibling implementation slices linked.

# Plan
- [x] 1. Start with channel config loading so ingestion has explicit inputs.
- [x] 2. Introduce a mockable YouTube metadata client and response normalizer.
- [x] 3. Add SQLite repository functions for idempotent channel, video, and pipeline run persistence.
- [x] 4. Replace the `ingest` and `candidates` placeholders with working CLI behavior.
- [x] 5. Add tests around mocked ingestion and candidate listing, then update README and close the Logics chain after validation.
- [x] ADR 009 checkpoint: update affected Logics docs during each meaningful wave and leave the repo commit-ready.
- [x] Keep commit creation under operator control; do not force one commit per micro-step.
- [x] GATE: do not close until lint, audit, and scaffold validation pass.

# Backlog
- `item_005_load_channel_configuration_for_ingestion`
- `item_006_create_bounded_youtube_metadata_client`
- `item_007_persist_ingested_channels_and_videos`
- `item_008_implement_ingest_and_candidates_cli_commands`
- `item_009_add_ingestion_tests_and_documentation`

# Definition of Done (DoD)
- [x] Generated request, product, backlog, and task docs are present.
- [x] Context-pack handoff is available when requested.
- [x] Validation passes.
- [x] Meaningful waves followed ADR 009: affected docs updated and the repo left commit-ready without automatic commits.

# AC Traceability
- request-AC1 -> This obsolete task. Proof: superseded by `req_003_mvp_single_video_local_first_pipeline`; channel configuration is no longer base-MVP scope.
- request-AC2 -> This obsolete task. Proof: superseded by `req_003_mvp_single_video_local_first_pipeline`; YouTube Data API ingestion is no longer base-MVP scope.
- request-AC3 -> This obsolete task. Proof: superseded by `req_003_mvp_single_video_local_first_pipeline`; recent channel video ingestion is no longer base-MVP scope.
- request-AC4 -> This obsolete task. Proof: superseded by `req_003_mvp_single_video_local_first_pipeline`; channel/video batch metadata persistence is replaced by single-video run state.
- request-AC5 -> This obsolete task. Proof: superseded by `req_003_mvp_single_video_local_first_pipeline`; pipeline run records now target single-video run steps.
- request-AC6 -> This obsolete task. Proof: superseded by `req_003_mvp_single_video_local_first_pipeline`; candidate listing is no longer base-MVP scope.
- request-AC7 -> This obsolete task. Proof: superseded by `req_003_mvp_single_video_local_first_pipeline`; deterministic tests move to the new single-video MVP validation slice.
- request-AC8 -> This obsolete task. Proof: superseded by `req_003_mvp_single_video_local_first_pipeline`; README now documents the single-video MVP path.
- request-AC9 -> This task. Evidence needed: The implementation remains local-first and VPS-ready: no hardcoded localhost-only assumptions, file paths are configurable, and secrets are not persisted in generated outputs.
- request-AC10 -> This task. Evidence needed: Tests cover URL parsing, subtitle-unavailable failure, transcript cleanup, OpenAI client boundaries, brief rendering, and HTML process-state rendering without live network calls.

# Validation
- Run `python3 -m logics_manager lint --require-status`.
- Run scaffold command tests.

# Report
- Implementation complete.

# AI Context
- Summary: Orchestrate Milestone 2 Metadata Ingestion
- Keywords: scaffolded-task, request-chain-scaffold, orchestration
- Use when: Coordinating implementation of a scaffolded request chain.
- Skip when: Working on one isolated sibling slice.

# Links
- Request: `req_001_milestone_2_metadata_ingestion`
- Product brief(s): `prod_002_claimlens_metadata_ingestion`
- Architecture decision(s): (none yet)
- Superseded by: `task_004_orchestrate_single_video_local_first_mvp`
