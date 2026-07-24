## item_069_simplify_progress_and_diagnostic_presentation - Simplify progress and diagnostic presentation
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Medium
> Theme: Status clarity
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- The stepper, step table, and jobs card repeat overlapping status information and surface implementation identifiers directly.

# Scope
- In:
  - Choose one primary progression representation.
  - Provide a collapsible or secondary diagnostic history.
  - Map pipeline identifiers to concise English product labels and accessible state text.
- Out:
  - Removing diagnostic data needed for support or troubleshooting.

# Acceptance criteria
- Progress is understandable without comparing multiple widgets.
- Status remains understandable with color disabled or unavailable.

# AC Traceability
- request-AC2 -> This backlog slice. Proof: Progress is understandable without comparing multiple widgets.
- request-AC3 -> This backlog slice. Proof: Status remains understandable with color disabled or unavailable.
- request-AC8 -> This backlog slice. Proof: Status remains understandable with color disabled or unavailable.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_015_focused_english_language_claimlens_analysis_workspace`
- Architecture decision(s): (none yet)
- Request: `req_011_refine_the_claimlens_analysis_workspace_user_experience`
- Primary task(s): `task_012_orchestrate_the_claimlens_analysis_workspace_ux_refinement`

# AI Context
- Summary: Simplify progress and diagnostic presentation
- Keywords: scaffolded-backlog, simplify progress and diagnostic presentation, implementation-ready
- Use when: Implementing the scaffolded slice for Simplify progress and diagnostic presentation.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.

# Tasks
- `task_012_orchestrate_the_claimlens_analysis_workspace_ux_refinement`

# Notes
- Task `task_012_orchestrate_the_claimlens_analysis_workspace_ux_refinement` was finished via `logics-manager flow finish task` on 2026-07-24.
