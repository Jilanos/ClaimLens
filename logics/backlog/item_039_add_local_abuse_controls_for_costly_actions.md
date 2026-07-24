## item_039_add_local_abuse_controls_for_costly_actions - Add local abuse controls for costly actions
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Medium
> Theme: Abuse prevention
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- A single authenticated or local user could repeatedly trigger outbound YouTube and OpenAI work.
- The future B1/B2 deployment decisions may add stronger perimeter controls, but the app still needs local guardrails.

# Scope
- In:
  - Add application-level rate limiting or quota checks for expensive actions.
  - Make limits configurable and document their relationship to future reverse-proxy controls.
  - Integrate limits with asynchronous jobs so rejected or queued work is explicit.
  - Ensure repeated submissions cannot bypass idempotence controls.
- Out:
  - Full billing, account management, or per-seat SaaS quotas.
  - Replacing future reverse-proxy or login controls.

# Acceptance criteria
- AC1: Expensive actions are rate-limited or quota-guarded by configurable application rules.
- AC2: Rejected actions return controlled user-facing messages.
- AC3: Logs record rate-limit decisions without secrets.
- AC4: Tests cover allowed, rejected, and duplicate-submission paths.

# AC Traceability
- request-AC10 -> This backlog slice. Proof: AC1: Expensive actions are rate-limited or quota-guarded by configurable application rules.
- request-AC15 -> This backlog slice. Proof: AC2: Rejected actions return controlled user-facing messages.
- request-AC16 -> This backlog slice. Proof: AC3: Logs record rate-limit decisions without secrets.
- request-AC18 -> This backlog slice. Proof: AC4: Tests cover allowed, rejected, and duplicate-submission paths.
- request-AC5 -> This backlog slice. Evidence needed: The analysis step bounds or chunks long transcripts, uses deterministic OpenAI settings where supported, and grounds each extracted notable claim with a transcript excerpt.
- request-AC6 -> This backlog slice. Evidence needed: YouTube channel-page scraping helpers that are outside the single-video MVP are isolated, disabled, or removed from exposed flows before online use.
- request-AC7 -> This backlog slice. Evidence needed: Source verification no longer relies on simple keyword polarity heuristics for supports/contradicts decisions and uses a review-aid vocabulary when evidence quality is insufficient.
- request-AC8 -> This backlog slice. Evidence needed: PubMed verification retrieves and stores real abstract/snippet evidence when available instead of treating titles as abstracts, and tests cover no-abstract fallback behavior.
- request-AC9 -> This backlog slice. Evidence needed: Verification confidence values are either removed or computed from documented evidence rules, and adapter/search errors are logged and surfaced distinctly from no-source results.
- request-AC11 -> This backlog slice. Evidence needed: The process page has accessible labels, responsive layout improvements, controlled user-facing error messages, source video links, cleaned-transcript preview, and paginated or bounded run selection.
- request-AC12 -> This backlog slice. Evidence needed: SQLite connections use WAL and busy_timeout for concurrent web access, while migration behavior is formalized with versioned, tested migration steps before the next schema change.
- request-AC13 -> This backlog slice. Evidence needed: Network and OpenAI failures including URLError, timeouts, malformed API responses, and adapter failures return controlled errors and structured logs without leaking internals to the UI.
- request-AC14 -> This backlog slice. Evidence needed: Runtime configuration does not depend on Path.cwd() in production paths and documents explicit environment/config-file precedence for deployed execution.
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
- Summary: Add local abuse controls for costly actions
- Keywords: scaffolded-backlog, add local abuse controls for costly actions, implementation-ready
- Use when: Implementing the scaffolded slice for Add local abuse controls for costly actions.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.

# Tasks
- `task_006_orchestrate_online_readiness_audit_implementation`

# Notes
- Task `task_006_orchestrate_online_readiness_audit_implementation` was finished via `logics-manager flow finish task` on 2026-07-24.
