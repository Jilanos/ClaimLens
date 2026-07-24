## item_071_add_an_evidence_aware_results_summary - Add an evidence-aware results summary
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Medium
> Theme: Result comprehension
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- Output links and raw source counts do not quickly tell an editor whether a report is normal, evidence-backed, or an incomplete verification attempt.

# Scope
- In:
  - Summarize brief availability, claims, evidence counts, adapter warnings, and report type.
  - Use explicit English labels for verification attempts and warnings.
  - Keep report view and download actions available.
- Out:
  - Changing source-verification verdict logic or presenting medical advice.

# Acceptance criteria
- A user can distinguish an evidence-backed report from an incomplete verification attempt before opening it.
- Warnings state the affected provider and a useful next action when one exists.

# AC Traceability
- request-AC5 -> This backlog slice. Proof: A user can distinguish an evidence-backed report from an incomplete verification attempt before opening it.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_015_focused_english_language_claimlens_analysis_workspace`
- Architecture decision(s): (none yet)
- Request: `req_011_refine_the_claimlens_analysis_workspace_user_experience`
- Primary task(s): `task_012_orchestrate_the_claimlens_analysis_workspace_ux_refinement`

# AI Context
- Summary: Add an evidence-aware results summary
- Keywords: scaffolded-backlog, add an evidence-aware results summary, implementation-ready
- Use when: Implementing the scaffolded slice for Add an evidence-aware results summary.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.

# Tasks
- `task_012_orchestrate_the_claimlens_analysis_workspace_ux_refinement`

# Notes
- Task `task_012_orchestrate_the_claimlens_analysis_workspace_ux_refinement` was finished via `logics-manager flow finish task` on 2026-07-24.
