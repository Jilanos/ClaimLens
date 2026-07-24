## item_034_improve_source_verification_evidence_quality - Improve source verification evidence quality
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: High
> Theme: Source verification
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- Verification polarity currently relies on fragile keyword matching.
- PubMed evidence can degrade to title-only snippets while still being treated like source evidence.
- Hard-coded confidence scores create false precision, and adapter errors are indistinguishable from no results.

# Scope
- In:
  - Replace simple keyword polarity with a more reliable evidence assessment boundary, preferably grounded on retrieved abstracts/snippets and mockable in tests.
  - Retrieve PubMed abstracts or structured snippets where available and store fallback provenance when abstracts are unavailable.
  - Remove confidence scores or compute them from documented evidence rules.
  - Use review-aid vocabulary when evidence is incomplete or heuristic.
  - Log adapter failures and surface adapter-error state separately from no-source state.
- Out:
  - Claiming automated scientific or medical authority.
  - Live PubMed or Semantic Scholar calls in CI.
  - Adding unrelated source providers.

# Acceptance criteria
- AC1: Verification decisions no longer depend on raw keyword polarity alone.
- AC2: PubMed evidence uses abstracts/snippets when available and records fallback state otherwise.
- AC3: Confidence output is removed or backed by documented rules.
- AC4: Adapter errors are logged and visible as errors, not silent no-source outcomes.
- AC5: Tests cover supported, contradicted, mixed, unclear, no-source, no-abstract, and adapter-error paths.

# AC Traceability
- request-AC7 -> This backlog slice. Proof: AC1: Verification decisions no longer depend on raw keyword polarity alone.
- request-AC8 -> This backlog slice. Proof: AC2: PubMed evidence uses abstracts/snippets when available and records fallback state otherwise.
- request-AC9 -> This backlog slice. Proof: AC3: Confidence output is removed or backed by documented rules.
- request-AC13 -> This backlog slice. Proof: AC4: Adapter errors are logged and visible as errors, not silent no-source outcomes.
- request-AC18 -> This backlog slice. Proof: AC5: Tests cover supported, contradicted, mixed, unclear, no-source, no-abstract, and adapter-error paths.
- request-AC6 -> This backlog slice. Evidence needed: YouTube channel-page scraping helpers that are outside the single-video MVP are isolated, disabled, or removed from exposed flows before online use.
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
- Summary: Improve source verification evidence quality
- Keywords: scaffolded-backlog, improve source verification evidence quality, implementation-ready
- Use when: Implementing the scaffolded slice for Improve source verification evidence quality.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.

# Tasks
- `task_006_orchestrate_online_readiness_audit_implementation`

# Notes
- Task `task_006_orchestrate_online_readiness_audit_implementation` was finished via `logics-manager flow finish task` on 2026-07-24.
