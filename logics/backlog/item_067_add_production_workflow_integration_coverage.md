## item_067_add_production_workflow_integration_coverage - Add production workflow integration coverage
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Medium
> Theme: Regression prevention
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- Current unit tests do not verify the actual HTTP polling lifecycle, restart recovery, or deployment-sensitive client identity behavior.

# Scope
- In:
  - Add deterministic HTTP integration tests for polling authorization and terminal updates.
  - Add restart, stale-job, configuration, cooldown, and report-semantic regression tests.
  - Document the supported operational behavior and validation commands.
- Out:
  - Live API calls in CI.
  - Browser visual regression infrastructure beyond the critical workflow coverage.

# Acceptance criteria
- The focused integration suite reproduces the previously stuck-job condition and proves the recovery behavior.
- All repository and Logics validation commands pass without external credentials.

# AC Traceability
- request-AC10 -> This backlog slice. Proof: The focused integration suite reproduces the previously stuck-job condition and proves the recovery behavior.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_014_reliable_claimlens_jobs_and_evidence_aware_reports`
- Architecture decision(s): (none yet)
- Request: `req_010_harden_claimlens_production_reliability_and_verification_integrity`
- Primary task(s): `task_011_orchestrate_production_reliability_and_verification_integrity_hardening`

# AI Context
- Summary: Add production workflow integration coverage
- Keywords: scaffolded-backlog, add production workflow integration coverage, implementation-ready
- Use when: Implementing the scaffolded slice for Add production workflow integration coverage.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.

# Tasks
- `task_011_orchestrate_production_reliability_and_verification_integrity_hardening`

# Notes
- Task `task_011_orchestrate_production_reliability_and_verification_integrity_hardening` was finished via `logics-manager flow finish task` on 2026-07-24.
