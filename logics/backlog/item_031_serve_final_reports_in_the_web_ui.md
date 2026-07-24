## item_031_serve_final_reports_in_the_web_ui - Serve final reports in the web UI
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Medium
> Theme: Report delivery
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- The web UI only displays a filesystem path for generated briefs.
- There is no route to view or download the final report, and serving files incorrectly would create path traversal risk.

# Scope
- In:
  - Add a route to render the generated Markdown brief as escaped/sanitized HTML.
  - Add a Markdown download route with safe Content-Disposition.
  - Resolve reports by validated run or video identifiers and verify resolved paths stay within the briefs directory.
  - Add clear empty, missing, and stale-report states in the web UI.
- Out:
  - PDF export unless a lightweight local dependency already exists and can be validated.
  - Public unauthenticated report sharing.

# Acceptance criteria
- AC1: A completed run exposes a browser-viewable final report.
- AC2: A completed run exposes a Markdown download.
- AC3: Path traversal attempts cannot read files outside outputs/briefs.
- AC4: Tests cover existing, missing, and invalid report references.

# AC Traceability
- request-AC2 -> This backlog slice. Proof: AC1: A completed run exposes a browser-viewable final report.
- request-AC11 -> This backlog slice. Proof: AC2: A completed run exposes a Markdown download.
- request-AC18 -> This backlog slice. Proof: AC3: Path traversal attempts cannot read files outside outputs/briefs.
- request-AC4 -> This backlog slice. Evidence needed: Single-video reports include real available video metadata such as title, source URL, author/channel, date, and duration when retrievable, while preserving graceful fallback behavior.
- request-AC5 -> This backlog slice. Evidence needed: The analysis step bounds or chunks long transcripts, uses deterministic OpenAI settings where supported, and grounds each extracted notable claim with a transcript excerpt.
- request-AC6 -> This backlog slice. Evidence needed: YouTube channel-page scraping helpers that are outside the single-video MVP are isolated, disabled, or removed from exposed flows before online use.
- request-AC7 -> This backlog slice. Evidence needed: Source verification no longer relies on simple keyword polarity heuristics for supports/contradicts decisions and uses a review-aid vocabulary when evidence quality is insufficient.
- request-AC8 -> This backlog slice. Evidence needed: PubMed verification retrieves and stores real abstract/snippet evidence when available instead of treating titles as abstracts, and tests cover no-abstract fallback behavior.
- request-AC9 -> This backlog slice. Evidence needed: Verification confidence values are either removed or computed from documented evidence rules, and adapter/search errors are logged and surfaced distinctly from no-source results.
- request-AC10 -> This backlog slice. Evidence needed: Long-running analyze/verify/report actions run through an asynchronous job model with persisted status, retry-safe/idempotent behavior, polling or equivalent UI updates, and user-visible progress states.
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
- Summary: Serve final reports in the web UI
- Keywords: scaffolded-backlog, serve final reports in the web ui, implementation-ready
- Use when: Implementing the scaffolded slice for Serve final reports in the web UI.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.

# Tasks
- `task_006_orchestrate_online_readiness_audit_implementation`

# Notes
- Task `task_006_orchestrate_online_readiness_audit_implementation` was finished via `logics-manager flow finish task` on 2026-07-24.
