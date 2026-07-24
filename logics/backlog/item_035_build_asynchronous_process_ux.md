## item_035_build_asynchronous_process_ux - Build asynchronous process UX
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: High
> Theme: Web UX
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- Long-running actions execute inside the HTTP request thread and leave the user without meaningful progress feedback.
- Concurrent duplicate actions can trigger duplicate paid or outbound work.

# Scope
- In:
  - Introduce a local asynchronous job model for analyze, verify, and report generation actions.
  - Persist job state, progress, failure causes, and output references.
  - Expose polling or equivalent web updates with loading, queued, running, failed, and completed states.
  - Make action submission idempotent enough to prevent duplicate concurrent paid calls for the same run/action.
  - Document recovery behavior for failed or interrupted jobs.
- Out:
  - Distributed queue infrastructure.
  - Multi-node deployment.
  - User-account-specific job dashboards.

# Acceptance criteria
- AC1: Analyze, verify, and report actions can run outside the request thread.
- AC2: The UI shows useful progress and terminal states.
- AC3: Duplicate concurrent action submissions do not duplicate paid/outbound work.
- AC4: Tests cover job creation, status transitions, polling rendering, and failure display.

# AC Traceability
- request-AC10 -> This backlog slice. Proof: AC1: Analyze, verify, and report actions can run outside the request thread.
- request-AC11 -> This backlog slice. Proof: AC2: The UI shows useful progress and terminal states.
- request-AC16 -> This backlog slice. Proof: AC3: Duplicate concurrent action submissions do not duplicate paid/outbound work.
- request-AC18 -> This backlog slice. Proof: AC4: Tests cover job creation, status transitions, polling rendering, and failure display.
- request-AC5 -> This backlog slice. Evidence needed: The analysis step bounds or chunks long transcripts, uses deterministic OpenAI settings where supported, and grounds each extracted notable claim with a transcript excerpt.
- request-AC6 -> This backlog slice. Evidence needed: YouTube channel-page scraping helpers that are outside the single-video MVP are isolated, disabled, or removed from exposed flows before online use.
- request-AC7 -> This backlog slice. Evidence needed: Source verification no longer relies on simple keyword polarity heuristics for supports/contradicts decisions and uses a review-aid vocabulary when evidence quality is insufficient.
- request-AC8 -> This backlog slice. Evidence needed: PubMed verification retrieves and stores real abstract/snippet evidence when available instead of treating titles as abstracts, and tests cover no-abstract fallback behavior.
- request-AC9 -> This backlog slice. Evidence needed: Verification confidence values are either removed or computed from documented evidence rules, and adapter/search errors are logged and surfaced distinctly from no-source results.
- request-AC12 -> This backlog slice. Evidence needed: SQLite connections use WAL and busy_timeout for concurrent web access, while migration behavior is formalized with versioned, tested migration steps before the next schema change.
- request-AC13 -> This backlog slice. Evidence needed: Network and OpenAI failures including URLError, timeouts, malformed API responses, and adapter failures return controlled errors and structured logs without leaking internals to the UI.
- request-AC14 -> This backlog slice. Evidence needed: Runtime configuration does not depend on Path.cwd() in production paths and documents explicit environment/config-file precedence for deployed execution.
- request-AC15 -> This backlog slice. Evidence needed: Rate limiting or quota enforcement exists for costly/outbound actions at the application boundary, with documentation of any remaining reverse-proxy dependency.
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
- Summary: Build asynchronous process UX
- Keywords: scaffolded-backlog, build asynchronous process ux, implementation-ready
- Use when: Implementing the scaffolded slice for Build asynchronous process UX.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.

# Tasks
- `task_006_orchestrate_online_readiness_audit_implementation`

# Notes
- Task `task_006_orchestrate_online_readiness_audit_implementation` was finished via `logics-manager flow finish task` on 2026-07-24.
