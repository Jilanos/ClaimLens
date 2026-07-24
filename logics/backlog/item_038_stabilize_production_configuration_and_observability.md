## item_038_stabilize_production_configuration_and_observability - Stabilize production configuration and observability
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Medium
> Theme: Operations
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- Configuration loading depends on the current working directory.
- Production diagnostics are limited because access logging is disabled and errors are not structured.
- Python versions differ between local environment and CI expectations.

# Scope
- In:
  - Define explicit config-file discovery and environment override precedence for deployed execution.
  - Stop relying on Path.cwd() for production config paths.
  - Add structured application and access logs while ensuring secrets are redacted.
  - Align documented supported Python versions with CI and local development expectations.
- Out:
  - Host provisioning, systemd unit creation, or reverse-proxy config.
  - External log aggregation services.

# Acceptance criteria
- AC1: Config loading works from a non-repository current working directory when an explicit config path or environment is provided.
- AC2: Logs include request/action diagnostics and exclude secrets.
- AC3: Python version support is documented and CI-aligned.
- AC4: Tests cover config precedence and secret redaction where applicable.

# AC Traceability
- request-AC13 -> This backlog slice. Proof: AC1: Config loading works from a non-repository current working directory when an explicit config path or environment is provided.
- request-AC14 -> This backlog slice. Proof: AC2: Logs include request/action diagnostics and exclude secrets.
- request-AC17 -> This backlog slice. Proof: AC3: Python version support is documented and CI-aligned.
- request-AC18 -> This backlog slice. Proof: AC4: Tests cover config precedence and secret redaction where applicable.
- request-AC5 -> This backlog slice. Evidence needed: The analysis step bounds or chunks long transcripts, uses deterministic OpenAI settings where supported, and grounds each extracted notable claim with a transcript excerpt.
- request-AC6 -> This backlog slice. Evidence needed: YouTube channel-page scraping helpers that are outside the single-video MVP are isolated, disabled, or removed from exposed flows before online use.
- request-AC7 -> This backlog slice. Evidence needed: Source verification no longer relies on simple keyword polarity heuristics for supports/contradicts decisions and uses a review-aid vocabulary when evidence quality is insufficient.
- request-AC8 -> This backlog slice. Evidence needed: PubMed verification retrieves and stores real abstract/snippet evidence when available instead of treating titles as abstracts, and tests cover no-abstract fallback behavior.
- request-AC9 -> This backlog slice. Evidence needed: Verification confidence values are either removed or computed from documented evidence rules, and adapter/search errors are logged and surfaced distinctly from no-source results.
- request-AC10 -> This backlog slice. Evidence needed: Long-running analyze/verify/report actions run through an asynchronous job model with persisted status, retry-safe/idempotent behavior, polling or equivalent UI updates, and user-visible progress states.
- request-AC11 -> This backlog slice. Evidence needed: The process page has accessible labels, responsive layout improvements, controlled user-facing error messages, source video links, cleaned-transcript preview, and paginated or bounded run selection.
- request-AC12 -> This backlog slice. Evidence needed: SQLite connections use WAL and busy_timeout for concurrent web access, while migration behavior is formalized with versioned, tested migration steps before the next schema change.
- request-AC15 -> This backlog slice. Evidence needed: Rate limiting or quota enforcement exists for costly/outbound actions at the application boundary, with documentation of any remaining reverse-proxy dependency.
- request-AC16 -> This backlog slice. Evidence needed: Re-analysis avoids unbounded duplicate summaries/claims and prevents duplicate concurrent paid calls for the same run/action.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_006_claimlens_online_readiness_audit_implementation`
- Architecture decision(s): (none yet)
- Request: `req_005_online_readiness_audit_implementation`
- Primary task(s): `task_006_orchestrate_online_readiness_audit_implementation`

# AI Context
- Summary: Stabilize production configuration and observability
- Keywords: scaffolded-backlog, stabilize production configuration and observability, implementation-ready
- Use when: Implementing the scaffolded slice for Stabilize production configuration and observability.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.

# Tasks
- `task_006_orchestrate_online_readiness_audit_implementation`

# Notes
- Task `task_006_orchestrate_online_readiness_audit_implementation` was finished via `logics-manager flow finish task` on 2026-07-24.
