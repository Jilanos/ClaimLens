## item_032_configure_report_language_and_enrich_video_metadata - Configure report language and enrich video metadata
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Medium
> Theme: Report content
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- Final reports currently do not have an explicit output-language contract.
- Single-video reports use the video id as title and lack source metadata.
- Out-of-scope channel scraping helpers remain present around exposed flows.

# Scope
- In:
  - Add a configurable final report language option in config, CLI, and web flow where appropriate.
  - Pass report language into LLM analysis and/or brief rendering with deterministic tests.
  - Retrieve or persist available video title, source URL, author/channel, publication date, and duration for single-video runs when a bounded metadata source is available.
  - Keep graceful fallback behavior when metadata cannot be retrieved.
  - Disable, isolate, or remove channel-page scraping from online-facing flows.
- Out:
  - Configurable transcript language as a required deliverable.
  - A broad YouTube channel ingestion product.
  - Live YouTube integration tests in CI.

# Acceptance criteria
- AC1: The final report language can be configured and is visible in generated output behavior.
- AC2: Reports show real metadata when available and safe fallbacks otherwise.
- AC3: Channel scraping is not exposed as part of the online MVP flow.
- AC4: Tests cover report-language propagation, metadata fallback, and exposed-flow boundaries.

# AC Traceability
- request-AC3 -> This backlog slice. Proof: AC1: The final report language can be configured and is visible in generated output behavior.
- request-AC4 -> This backlog slice. Proof: AC2: Reports show real metadata when available and safe fallbacks otherwise.
- request-AC6 -> This backlog slice. Proof: AC3: Channel scraping is not exposed as part of the online MVP flow.
- request-AC18 -> This backlog slice. Proof: AC4: Tests cover report-language propagation, metadata fallback, and exposed-flow boundaries.
- request-AC5 -> This backlog slice. Evidence needed: The analysis step bounds or chunks long transcripts, uses deterministic OpenAI settings where supported, and grounds each extracted notable claim with a transcript excerpt.
- request-AC7 -> This backlog slice. Evidence needed: Source verification no longer relies on simple keyword polarity heuristics for supports/contradicts decisions and uses a review-aid vocabulary when evidence quality is insufficient.
- request-AC8 -> This backlog slice. Evidence needed: PubMed verification retrieves and stores real abstract/snippet evidence when available instead of treating titles as abstracts, and tests cover no-abstract fallback behavior.
- request-AC9 -> This backlog slice. Evidence needed: Verification confidence values are either removed or computed from documented evidence rules, and adapter/search errors are logged and surfaced distinctly from no-source results.
- request-AC10 -> This backlog slice. Evidence needed: Long-running analyze/verify/report actions run through an asynchronous job model with persisted status, retry-safe/idempotent behavior, polling or equivalent UI updates, and user-visible progress states.
- request-AC11 -> This backlog slice. Evidence needed: The process page has accessible labels, responsive layout improvements, controlled user-facing error messages, source video links, cleaned-transcript preview, and paginated or bounded run selection.
- request-AC12 -> This backlog slice. Evidence needed: SQLite connections use WAL and busy_timeout for concurrent web access, while migration behavior is formalized with versioned, tested migration steps before the next schema change.
- request-AC13 -> This backlog slice. Evidence needed: Network and OpenAI failures including URLError, timeouts, malformed API responses, and adapter failures return controlled errors and structured logs without leaking internals to the UI.
- request-AC14 -> This backlog slice. Evidence needed: Runtime configuration does not depend on Path.cwd() in production paths and documents explicit environment/config-file precedence for deployed execution.
- request-AC15 -> This backlog slice. Evidence needed: Rate limiting or quota enforcement exists for costly/outbound actions at the application boundary, with documentation of any remaining reverse-proxy dependency.
- request-AC16 -> This backlog slice. Evidence needed: Re-analysis avoids unbounded duplicate summaries/claims and prevents duplicate concurrent paid calls for the same run/action.
- request-AC17 -> This backlog slice. Evidence needed: Structured application/access logging is available for online diagnostics without persisting secrets, and Python version expectations are aligned across local docs and CI.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_006_claimlens_online_readiness_audit_implementation`
- Architecture decision(s): (none yet)
- Request: `req_005_online_readiness_audit_implementation`
- Primary task(s): `task_006_orchestrate_online_readiness_audit_implementation`

# AI Context
- Summary: Configure report language and enrich video metadata
- Keywords: scaffolded-backlog, configure report language and enrich video metadata, implementation-ready
- Use when: Implementing the scaffolded slice for Configure report language and enrich video metadata.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.

# Tasks
- `task_006_orchestrate_online_readiness_audit_implementation`

# Notes
- Task `task_006_orchestrate_online_readiness_audit_implementation` was finished via `logics-manager flow finish task` on 2026-07-24.
