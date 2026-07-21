## item_006_create_bounded_youtube_metadata_client - Create bounded YouTube metadata client
> From version: 1.0.0
> Schema version: 1.0
> Status: Ready
> Understanding: 90%
> Confidence: 85%
> Progress: 0%
> Complexity: Medium
> Theme: Ingestion
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- The pipeline needs YouTube metadata, but external API access must be isolated for testing and later rate-limit handling.

# Scope
- In:
  - YouTube Data API client abstraction.
  - API key validation for real calls.
  - Fetch recent videos per configured channel.
  - Normalize API responses into internal records.
  - Mockable tests for successful and empty responses.
- Out:
  - OAuth flows.
  - Caption retrieval.
  - Video comments.
  - Quota dashboarding beyond clear error messages.

# Acceptance criteria
- AC1: Real client construction requires `YOUTUBE_API_KEY`.
- AC2: The ingestion module depends on a protocol or injectable client for tests.
- AC3: Recent video responses are normalized into stable internal objects.
- AC4: Tests cover the client boundary without network calls.

# AC Traceability
- request-AC2 -> This backlog slice. Proof: AC1: Real client construction requires `YOUTUBE_API_KEY`.
- request-AC3 -> This backlog slice. Proof: AC2: The ingestion module depends on a protocol or injectable client for tests.
- request-AC7 -> This backlog slice. Proof: AC3: Recent video responses are normalized into stable internal objects.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_002_claimlens_metadata_ingestion`
- Architecture decision(s): (none yet)
- Request: `req_001_milestone_2_metadata_ingestion`
- Primary task(s): `task_002_orchestrate_milestone_2_metadata_ingestion`

# AI Context
- Summary: Create bounded YouTube metadata client
- Keywords: scaffolded-backlog, create bounded youtube metadata client, implementation-ready
- Use when: Implementing the scaffolded slice for Create bounded YouTube metadata client.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.
