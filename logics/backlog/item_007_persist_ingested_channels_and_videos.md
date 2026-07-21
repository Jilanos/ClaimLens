## item_007_persist_ingested_channels_and_videos - Persist ingested channels and videos
> From version: 1.0.0
> Schema version: 1.0
> Status: Ready
> Understanding: 90%
> Confidence: 85%
> Progress: 0%
> Complexity: Medium
> Theme: Storage
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- Ingestion should be repeatable and should not create duplicate records when the same video appears in multiple runs.

# Scope
- In:
  - Repository functions for channel upserts.
  - Repository functions for video upserts.
  - Pipeline run recording for ingest success and failure.
  - Tests for idempotent persistence.
- Out:
  - Schema migrations beyond additive changes if avoidable.
  - Deleting stale videos.
  - Complex status transitions outside ingestion.

# Acceptance criteria
- AC1: Inserting the same channel twice keeps one channel row.
- AC2: Inserting the same video twice keeps one video row and updates mutable metadata.
- AC3: Ingest success and failure paths write pipeline run records.
- AC4: Persistence tests run against temporary SQLite databases.

# AC Traceability
- request-AC4 -> This backlog slice. Proof: AC1: Inserting the same channel twice keeps one channel row.
- request-AC5 -> This backlog slice. Proof: AC2: Inserting the same video twice keeps one video row and updates mutable metadata.
- request-AC7 -> This backlog slice. Proof: AC3: Ingest success and failure paths write pipeline run records.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_002_claimlens_metadata_ingestion`
- Architecture decision(s): (none yet)
- Request: `req_001_milestone_2_metadata_ingestion`
- Primary task(s): `task_002_orchestrate_milestone_2_metadata_ingestion`

# AI Context
- Summary: Persist ingested channels and videos
- Keywords: scaffolded-backlog, persist ingested channels and videos, implementation-ready
- Use when: Implementing the scaffolded slice for Persist ingested channels and videos.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.
