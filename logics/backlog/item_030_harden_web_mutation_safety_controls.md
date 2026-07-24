## item_030_harden_web_mutation_safety_controls - Harden web mutation safety controls
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Medium
> Theme: Web security
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- The current web POST handling accepts arbitrary Content-Length values, reads the full request body into memory, and has no CSRF control.
- Raw exceptions can currently reach the user-facing page.

# Scope
- In:
  - Validate Content-Length parsing and cap body size with configurable defaults.
  - Add CSRF tokens for mutating web forms and reject missing or invalid tokens.
  - Return controlled HTTP errors and UI messages for malformed, oversized, or unauthorized mutation attempts.
  - Add unit tests or integration tests for malformed length, oversized body, and CSRF rejection/acceptance.
- Out:
  - HTTPS, login, sessions backed by a user account store, and reverse-proxy setup.
  - OpenAI key ownership decisions.

# Acceptance criteria
- AC1: Oversized or malformed POST bodies are rejected before unbounded reads.
- AC2: Mutating web forms require valid CSRF tokens.
- AC3: User-facing errors are controlled and do not expose tracebacks or internal paths.
- AC4: Tests cover success and failure paths.

# AC Traceability
- request-AC1 -> This backlog slice. Proof: AC1: Oversized or malformed POST bodies are rejected before unbounded reads.
- request-AC13 -> This backlog slice. Proof: AC2: Mutating web forms require valid CSRF tokens.
- request-AC18 -> This backlog slice. Proof: AC3: User-facing errors are controlled and do not expose tracebacks or internal paths.
- request-AC4 -> This backlog slice. Evidence needed: Single-video reports include real available video metadata such as title, source URL, author/channel, date, and duration when retrievable, while preserving graceful fallback behavior.
- request-AC5 -> This backlog slice. Evidence needed: The analysis step bounds or chunks long transcripts, uses deterministic OpenAI settings where supported, and grounds each extracted notable claim with a transcript excerpt.
- request-AC6 -> This backlog slice. Evidence needed: YouTube channel-page scraping helpers that are outside the single-video MVP are isolated, disabled, or removed from exposed flows before online use.
- request-AC7 -> This backlog slice. Evidence needed: Source verification no longer relies on simple keyword polarity heuristics for supports/contradicts decisions and uses a review-aid vocabulary when evidence quality is insufficient.
- request-AC8 -> This backlog slice. Evidence needed: PubMed verification retrieves and stores real abstract/snippet evidence when available instead of treating titles as abstracts, and tests cover no-abstract fallback behavior.
- request-AC9 -> This backlog slice. Evidence needed: Verification confidence values are either removed or computed from documented evidence rules, and adapter/search errors are logged and surfaced distinctly from no-source results.
- request-AC10 -> This backlog slice. Evidence needed: Long-running analyze/verify/report actions run through an asynchronous job model with persisted status, retry-safe/idempotent behavior, polling or equivalent UI updates, and user-visible progress states.
- request-AC11 -> This backlog slice. Evidence needed: The process page has accessible labels, responsive layout improvements, controlled user-facing error messages, source video links, cleaned-transcript preview, and paginated or bounded run selection.
- request-AC12 -> This backlog slice. Evidence needed: SQLite connections use WAL and busy_timeout for concurrent web access, while migration behavior is formalized with versioned, tested migration steps before the next schema change.
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
- Summary: Harden web mutation safety controls
- Keywords: scaffolded-backlog, harden web mutation safety controls, implementation-ready
- Use when: Implementing the scaffolded slice for Harden web mutation safety controls.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.

# Tasks
- `task_006_orchestrate_online_readiness_audit_implementation`

# Notes
- Task `task_006_orchestrate_online_readiness_audit_implementation` was finished via `logics-manager flow finish task` on 2026-07-24.
