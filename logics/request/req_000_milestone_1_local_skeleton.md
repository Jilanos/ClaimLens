## req_000_milestone_1_local_skeleton - Milestone 1: Local Skeleton
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Complexity: Medium
> Theme: Foundation
> Reminder: Update status/understanding/confidence and linked backlog/task references when you edit this doc.

# Needs
- Create the first executable foundation for ClaimLens.
- Provide a local CLI that can initialize storage and expose the first planned pipeline commands.
- Keep implementation lightweight and auditable so later YouTube, OpenAI, and source-check modules can build on it.

# Context
- ClaimLens is an MVP for turning selected YouTube videos into sourced, claim-aware briefs.
- The initial stack is Python, SQLite, YouTube Data API, OpenAI API, source APIs, and Markdown output.
- Milestone 1 is limited to local project skeleton, CLI, config loading, SQLite schema, and developer commands.

# Acceptance criteria
- AC1: The repository contains a Python package skeleton with a runnable `claimlens` CLI entry point.
- AC2: `claimlens init-db` creates or migrates a local SQLite database without requiring external API keys.
- AC3: The initial SQLite schema includes tables for channels, videos, transcripts, summaries, claims, sources, claim-source links, and pipeline runs.
- AC4: Local configuration can be loaded from files and environment variables, with a documented example.
- AC5: Placeholder CLI commands exist for ingest, candidates, transcribe, analyze, source-check, brief, and run-daily, returning clear not-yet-implemented messages where needed.
- AC6: Developer commands are documented and include install, format/lint, test, and database initialization.
- AC7: Basic tests cover CLI startup, config loading, and database initialization.

# Definition of Ready (DoR)
- [x] Problem statement is explicit and user impact is clear.
- [x] Scope boundaries (in/out) are explicit.
- [x] Acceptance criteria are testable.
- [x] Dependencies and known risks are listed.

# Companion docs
- Product brief(s): `prod_001_claimlens_local_skeleton`
- Architecture decision(s): (none yet)

# References
- README.md
- ROADMAP.md

# AI Context
- Summary: Milestone 1: Local Skeleton
- Keywords: request-chain-scaffold, milestone 1: local skeleton, development-ready
- Use when: You need to implement or review the scaffolded workflow for Milestone 1: Local Skeleton.
- Skip when: The change is unrelated to this scaffolded request chain.

# Backlog
- `item_001_create_python_package_and_cli_shell`
- `item_002_implement_configuration_loading`
- `item_003_create_sqlite_schema_and_init_db_command`
- `item_004_add_baseline_test_and_quality_tooling`
