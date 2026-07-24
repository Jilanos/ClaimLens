## item_064_apply_source_verification_configuration_switches - Apply source-verification configuration switches
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Medium
> Theme: Configuration correctness
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- Source configuration flags are parsed but PubMed and Semantic Scholar adapters are always instantiated by the application workflows.

# Scope
- In:
  - Build adapters from SourceConfig for CLI and web paths.
  - Hide or reject unavailable verification actions with a clear message.
  - Test every enabled and disabled adapter combination.
- Out:
  - Adding a provider implementation without an explicit product decision.

# Acceptance criteria
- Disabled adapters receive no network calls and are absent from outcome reporting.
- The advanced verification switch has an observable, documented effect.

# AC Traceability
- request-AC5 -> This backlog slice. Proof: Disabled adapters receive no network calls and are absent from outcome reporting.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_014_reliable_claimlens_jobs_and_evidence_aware_reports`
- Architecture decision(s): (none yet)
- Request: `req_010_harden_claimlens_production_reliability_and_verification_integrity`
- Primary task(s): `task_011_orchestrate_production_reliability_and_verification_integrity_hardening`

# AI Context
- Summary: Apply source-verification configuration switches
- Keywords: scaffolded-backlog, apply source-verification configuration switches, implementation-ready
- Use when: Implementing the scaffolded slice for Apply source-verification configuration switches.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.

# Tasks
- `task_011_orchestrate_production_reliability_and_verification_integrity_hardening`

# Notes
- Task `task_011_orchestrate_production_reliability_and_verification_integrity_hardening` was finished via `logics-manager flow finish task` on 2026-07-24.
