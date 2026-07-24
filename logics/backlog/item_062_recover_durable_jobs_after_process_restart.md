## item_062_recover_durable_jobs_after_process_restart - Recover durable jobs after process restart
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: High
> Theme: Job durability
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- SQLite preserves queued and running job rows while the in-process executor loses them on restart, leaving runs permanently blocked from retrying the same action.

# Scope
- In:
  - Add durable job lease, heartbeat, stale-job reconciliation, and retryable terminal states.
  - Define a bounded execution timeout and Process-page representation for interrupted work.
  - Add startup and failure-path tests.
- Out:
  - Distributed task processing across arbitrary hosts.
  - Fine-grained percentage progress for opaque third-party calls.

# Acceptance criteria
- Restarting after job submission never leaves an unrepeatable queued or running action.
- The user can retry recovered work and sees an actionable interruption message.

# AC Traceability
- request-AC1 -> This backlog slice. Proof: Restarting after job submission never leaves an unrepeatable queued or running action.
- request-AC2 -> This backlog slice. Proof: The user can retry recovered work and sees an actionable interruption message.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_014_reliable_claimlens_jobs_and_evidence_aware_reports`
- Architecture decision(s): (none yet)
- Request: `req_010_harden_claimlens_production_reliability_and_verification_integrity`
- Primary task(s): `task_011_orchestrate_production_reliability_and_verification_integrity_hardening`

# AI Context
- Summary: Recover durable jobs after process restart
- Keywords: scaffolded-backlog, recover durable jobs after process restart, implementation-ready
- Use when: Implementing the scaffolded slice for Recover durable jobs after process restart.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: Critical
- Rationale: Set by scaffold input or defaulted for grooming.

# Tasks
- `task_011_orchestrate_production_reliability_and_verification_integrity_hardening`

# Notes
- Task `task_011_orchestrate_production_reliability_and_verification_integrity_hardening` was finished via `logics-manager flow finish task` on 2026-07-24.
