## item_068_create_a_focused_active_analysis_workspace - Create a focused active-analysis workspace
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: High
> Theme: Primary workflow
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- The Process page makes users scan through unrelated creation, selection, pipeline, job, and output cards before identifying what needs attention.

# Scope
- In:
  - Introduce a selected-run workspace header and action area.
  - Expose video identity, current state, live provider message, and one next action.
  - Move detailed operational information below the primary workspace.
- Out:
  - Changing background job execution semantics.
  - Adding realtime transport beyond existing polling.

# Acceptance criteria
- A user can identify the current video, state, and required next action without reading a table.
- Only one action is visually primary for a run at any given workflow state.

# AC Traceability
- request-AC1 -> This backlog slice. Proof: A user can identify the current video, state, and required next action without reading a table.
- request-AC2 -> This backlog slice. Proof: Only one action is visually primary for a run at any given workflow state.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_015_focused_english_language_claimlens_analysis_workspace`
- Architecture decision(s): (none yet)
- Request: `req_011_refine_the_claimlens_analysis_workspace_user_experience`
- Primary task(s): `task_012_orchestrate_the_claimlens_analysis_workspace_ux_refinement`

# AI Context
- Summary: Create a focused active-analysis workspace
- Keywords: scaffolded-backlog, create a focused active-analysis workspace, implementation-ready
- Use when: Implementing the scaffolded slice for Create a focused active-analysis workspace.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.

# Tasks
- `task_012_orchestrate_the_claimlens_analysis_workspace_ux_refinement`

# Notes
- Task `task_012_orchestrate_the_claimlens_analysis_workspace_ux_refinement` was finished via `logics-manager flow finish task` on 2026-07-24.
