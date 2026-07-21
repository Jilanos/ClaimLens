## item_008_implement_ingest_and_candidates_cli_commands - Implement ingest and candidates CLI commands
> From version: 1.0.0
> Schema version: 1.0
> Status: Ready
> Understanding: 90%
> Confidence: 85%
> Progress: 0%
> Complexity: Medium
> Theme: CLI
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- `claimlens ingest` and `claimlens candidates` are currently placeholders and do not operate on project data.

# Scope
- In:
  - `claimlens ingest` command implementation.
  - `claimlens candidates` command implementation.
  - Useful console output for imported and listed videos.
  - Command flags for config, channels file, database override, and basic limits where needed.
- Out:
  - Interactive video approval workflow.
  - Advanced scoring.
  - Transcript or analysis command implementation.

# Acceptance criteria
- AC1: `claimlens ingest` imports metadata for configured channels when API key and channel config are present.
- AC2: `claimlens ingest` exits clearly when the API key or channel config is missing.
- AC3: `claimlens candidates` lists videos from SQLite without requiring API keys.
- AC4: CLI tests cover success and error paths without network calls.

# AC Traceability
- request-AC2 -> This backlog slice. Proof: AC1: `claimlens ingest` imports metadata for configured channels when API key and channel config are present.
- request-AC3 -> This backlog slice. Proof: AC2: `claimlens ingest` exits clearly when the API key or channel config is missing.
- request-AC6 -> This backlog slice. Proof: AC3: `claimlens candidates` lists videos from SQLite without requiring API keys.
- request-AC8 -> This backlog slice. Proof: AC4: CLI tests cover success and error paths without network calls.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_002_claimlens_metadata_ingestion`
- Architecture decision(s): (none yet)
- Request: `req_001_milestone_2_metadata_ingestion`
- Primary task(s): `task_002_orchestrate_milestone_2_metadata_ingestion`

# AI Context
- Summary: Implement ingest and candidates CLI commands
- Keywords: scaffolded-backlog, implement ingest and candidates cli commands, implementation-ready
- Use when: Implementing the scaffolded slice for Implement ingest and candidates CLI commands.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.
