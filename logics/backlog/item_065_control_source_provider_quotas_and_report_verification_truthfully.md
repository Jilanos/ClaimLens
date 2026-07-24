## item_065_control_source_provider_quotas_and_report_verification_truthfully - Control source-provider quotas and report verification truthfully
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: High
> Theme: Verification resilience
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- Per-claim retries capped at three seconds can amplify HTTP 429 responses, while no-evidence attempts still create a .verified.md artifact.

# Scope
- In:
  - Implement provider-level cooldown, Retry-After handling, bounded retries, and remediation states.
  - Separate verified evidence reports from incomplete verification-attempt reports.
  - Expose adapter diagnostics in the UI and exported Markdown.
- Out:
  - Guaranteeing a research source for every claim.
  - Presenting literature candidates as medical advice.

# Acceptance criteria
- A 429 does not cause an early repeated request while the provider cooldown remains active.
- An all-warning result cannot be mistaken for a successful source-verified report.

# AC Traceability
- request-AC6 -> This backlog slice. Proof: A 429 does not cause an early repeated request while the provider cooldown remains active.
- request-AC7 -> This backlog slice. Proof: An all-warning result cannot be mistaken for a successful source-verified report.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_014_reliable_claimlens_jobs_and_evidence_aware_reports`
- Architecture decision(s): (none yet)
- Request: `req_010_harden_claimlens_production_reliability_and_verification_integrity`
- Primary task(s): `task_011_orchestrate_production_reliability_and_verification_integrity_hardening`

# AI Context
- Summary: Control source-provider quotas and report verification truthfully
- Keywords: scaffolded-backlog, control source-provider quotas and report verification truthfully, implementation-ready
- Use when: Implementing the scaffolded slice for Control source-provider quotas and report verification truthfully.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.

# Tasks
- `task_011_orchestrate_production_reliability_and_verification_integrity_hardening`

# Notes
- Task `task_011_orchestrate_production_reliability_and_verification_integrity_hardening` was finished via `logics-manager flow finish task` on 2026-07-24.
