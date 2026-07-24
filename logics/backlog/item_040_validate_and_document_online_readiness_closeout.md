## item_040_validate_and_document_online_readiness_closeout - Validate and document online readiness closeout
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Medium
> Theme: Validation
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- The accepted audit findings touch security, UI, persistence, external APIs, and operations; closeout needs a clear proof bundle.

# Scope
- In:
  - Update README, ROADMAP, and any deployment/operator notes affected by the implementation.
  - Record standby decisions for B1 OpenAI key model and B2 reverse-proxy HTTPS/login.
  - Run ruff, pytest, compileall where applicable, logics-manager lint --require-status, and logics-manager audit.
  - Add a manual smoke-test checklist for report view/download, async progress, verification errors, and rate limits.
- Out:
  - Actually deploying to the VPS.
  - Closing B1 or B2.

# Acceptance criteria
- AC1: Operator-facing documentation reflects the implemented behavior and remaining deployment standbys.
- AC2: Automated validation commands pass before closeout.
- AC3: Manual smoke-test steps are documented for the online-readiness path.
- AC4: Logics request, backlog, task, and context pack pass validation.

# AC Traceability
- request-AC18 -> This backlog slice. Proof: AC1: Operator-facing documentation reflects the implemented behavior and remaining deployment standbys.
- request-AC2 -> This backlog slice. Evidence needed: The web UI can display the generated Markdown brief as safe HTML and download it as Markdown through routes that resolve reports by validated run/video identifiers and prevent path traversal.
- request-AC3 -> This backlog slice. Evidence needed: Final report rendering language is configurable from CLI/config/web flow, persisted or passed through the run as appropriate, and covered by tests without requiring configurable subtitle language.
- request-AC4 -> This backlog slice. Evidence needed: Single-video reports include real available video metadata such as title, source URL, author/channel, date, and duration when retrievable, while preserving graceful fallback behavior.
- request-AC5 -> This backlog slice. Evidence needed: The analysis step bounds or chunks long transcripts, uses deterministic OpenAI settings where supported, and grounds each extracted notable claim with a transcript excerpt.
- request-AC6 -> This backlog slice. Evidence needed: YouTube channel-page scraping helpers that are outside the single-video MVP are isolated, disabled, or removed from exposed flows before online use.
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
- Summary: Validate and document online readiness closeout
- Keywords: scaffolded-backlog, validate and document online readiness closeout, implementation-ready
- Use when: Implementing the scaffolded slice for Validate and document online readiness closeout.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.

# Tasks
- `task_006_orchestrate_online_readiness_audit_implementation`

# Notes
- Task `task_006_orchestrate_online_readiness_audit_implementation` was finished via `logics-manager flow finish task` on 2026-07-24.
