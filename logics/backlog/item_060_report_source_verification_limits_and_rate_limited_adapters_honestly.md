## item_060_report_source_verification_limits_and_rate_limited_adapters_honestly - Report source verification limits and rate-limited adapters honestly
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: High
> Theme: Verification reliability
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- A Semantic Scholar HTTP 429 plus zero PubMed candidates produces a completed verified brief with no evidence, leaving the user unable to distinguish a negative finding from an unavailable adapter.

# Scope
- In:
  - Persist and render adapter-level result summaries.
  - Use a truthful terminal verification state for all-adapter failure and partial outcomes.
  - Add finite Semantic Scholar rate-limit handling and remediation guidance.
- Out:
  - Guaranteed retrieval of evidence for every exercise claim.
  - Replacing PubMed or Semantic Scholar with paid proprietary search.

# Acceptance criteria
- The F6OKdue0UBw outcome clearly reports Semantic Scholar HTTP 429 and PubMed no-candidate results.
- A brief is never labelled source-verified when all adapters failed.

# AC Traceability
- request-AC8 -> This backlog slice. Proof: The F6OKdue0UBw outcome clearly reports Semantic Scholar HTTP 429 and PubMed no-candidate results.
- request-AC9 -> This backlog slice. Proof: A brief is never labelled source-verified when all adapters failed.
- request-AC10 -> This backlog slice. Proof: A brief is never labelled source-verified when all adapters failed.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_013_live_claimlens_process_feedback_and_trustworthy_verification_results`
- Architecture decision(s): (none yet)
- Request: `req_009_make_process_state_live_and_verification_outcomes_actionable`
- Primary task(s): `task_010_orchestrate_live_process_feedback_and_verification_reliability_delivery`

# AI Context
- Summary: Report source verification limits and rate-limited adapters honestly
- Keywords: scaffolded-backlog, report source verification limits and rate-limited adapters honestly, implementation-ready
- Use when: Implementing the scaffolded slice for Report source verification limits and rate-limited adapters honestly.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.

# Tasks
- `task_010_orchestrate_live_process_feedback_and_verification_reliability_delivery`

# Notes
- Task `task_010_orchestrate_live_process_feedback_and_verification_reliability_delivery` was finished via `logics-manager flow finish task` on 2026-07-24.
