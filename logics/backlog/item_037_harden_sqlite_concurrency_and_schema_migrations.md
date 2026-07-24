## item_037_harden_sqlite_concurrency_and_schema_migrations - Harden SQLite concurrency and schema migrations
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Medium
> Theme: Persistence
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- SQLite is not configured with WAL or busy_timeout for concurrent web writes.
- Schema migration behavior is ad hoc and future schema changes need a versioned tested path.
- Re-analysis can accumulate duplicate summaries and claims.

# Scope
- In:
  - Enable WAL and busy_timeout on SQLite connections where safe.
  - Introduce or document versioned migration steps before the next schema change.
  - Add migration tests for existing database upgrades.
  - Make analysis summary/claim persistence idempotent or prune superseded records according to a documented policy.
- Out:
  - Replacing SQLite with another database.
  - Destructive migrations without explicit operator migration guidance.

# Acceptance criteria
- AC1: SQLite connections apply WAL and busy_timeout in normal operation.
- AC2: Schema migrations are versioned and tested against an older schema fixture or equivalent setup.
- AC3: Re-analysis does not grow summaries/claims without bound.
- AC4: Tests cover concurrency-relevant pragmas and migration paths.

# AC Traceability
- request-AC12 -> This backlog slice. Proof: AC1: SQLite connections apply WAL and busy_timeout in normal operation.
- request-AC16 -> This backlog slice. Proof: AC2: Schema migrations are versioned and tested against an older schema fixture or equivalent setup.
- request-AC18 -> This backlog slice. Proof: AC3: Re-analysis does not grow summaries/claims without bound.
- request-AC4 -> This backlog slice. Evidence needed: Single-video reports include real available video metadata such as title, source URL, author/channel, date, and duration when retrievable, while preserving graceful fallback behavior.
- request-AC5 -> This backlog slice. Evidence needed: The analysis step bounds or chunks long transcripts, uses deterministic OpenAI settings where supported, and grounds each extracted notable claim with a transcript excerpt.
- request-AC6 -> This backlog slice. Evidence needed: YouTube channel-page scraping helpers that are outside the single-video MVP are isolated, disabled, or removed from exposed flows before online use.
- request-AC7 -> This backlog slice. Evidence needed: Source verification no longer relies on simple keyword polarity heuristics for supports/contradicts decisions and uses a review-aid vocabulary when evidence quality is insufficient.
- request-AC8 -> This backlog slice. Evidence needed: PubMed verification retrieves and stores real abstract/snippet evidence when available instead of treating titles as abstracts, and tests cover no-abstract fallback behavior.
- request-AC9 -> This backlog slice. Evidence needed: Verification confidence values are either removed or computed from documented evidence rules, and adapter/search errors are logged and surfaced distinctly from no-source results.
- request-AC10 -> This backlog slice. Evidence needed: Long-running analyze/verify/report actions run through an asynchronous job model with persisted status, retry-safe/idempotent behavior, polling or equivalent UI updates, and user-visible progress states.
- request-AC11 -> This backlog slice. Evidence needed: The process page has accessible labels, responsive layout improvements, controlled user-facing error messages, source video links, cleaned-transcript preview, and paginated or bounded run selection.
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
- Summary: Harden SQLite concurrency and schema migrations
- Keywords: scaffolded-backlog, harden sqlite concurrency and schema migrations, implementation-ready
- Use when: Implementing the scaffolded slice for Harden SQLite concurrency and schema migrations.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.

# Tasks
- `task_006_orchestrate_online_readiness_audit_implementation`

# Notes
- Task `task_006_orchestrate_online_readiness_audit_implementation` was finished via `logics-manager flow finish task` on 2026-07-24.
