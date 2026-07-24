## item_057_add_bounded_live_process_job_state_refresh - Add bounded live Process job state refresh
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Medium
> Theme: Process UX
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- The Process page captures the job at submission time and never sees its later SQLite state, leaving a completed task displayed as running at 5%.

# Scope
- In:
  - Add a run-visible JSON status representation.
  - Poll only while the selected run has active jobs, then update the relevant Process UI state and stop.
  - Replace numeric job progress display with semantic status and message.
- Out:
  - WebSockets, server-sent events, and external job queues.
  - Fine-grained progress reporting for opaque external API calls.

# Acceptance criteria
- A completed background captions job becomes visible in the same open Process page without navigation or manual refresh.
- Polling is authorized, bounded, terminal-aware, and avoids rewriting unchanged state.

# AC Traceability
- request-AC1 -> This backlog slice. Proof: A completed background captions job becomes visible in the same open Process page without navigation or manual refresh.
- request-AC2 -> This backlog slice. Proof: Polling is authorized, bounded, terminal-aware, and avoids rewriting unchanged state.
- request-AC3 -> This backlog slice. Proof: Polling is authorized, bounded, terminal-aware, and avoids rewriting unchanged state.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_013_live_claimlens_process_feedback_and_trustworthy_verification_results`
- Architecture decision(s): (none yet)
- Request: `req_009_make_process_state_live_and_verification_outcomes_actionable`
- Primary task(s): `task_010_orchestrate_live_process_feedback_and_verification_reliability_delivery`

# AI Context
- Summary: Add bounded live Process job state refresh
- Keywords: scaffolded-backlog, add bounded live process job state refresh, implementation-ready
- Use when: Implementing the scaffolded slice for Add bounded live Process job state refresh.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.

# Tasks
- `task_010_orchestrate_live_process_feedback_and_verification_reliability_delivery`

# Notes
- Task `task_010_orchestrate_live_process_feedback_and_verification_reliability_delivery` was finished via `logics-manager flow finish task` on 2026-07-24.
