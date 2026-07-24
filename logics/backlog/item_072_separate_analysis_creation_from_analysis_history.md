## item_072_separate_analysis_creation_from_analysis_history - Separate analysis creation from analysis history
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: High
> Theme: Information architecture
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- Creating a run and loading a prior run are peer cards, so neither new work nor history is optimized for repeated use.

# Scope
- In:
  - Create a focused new-analysis entry point.
  - Provide recent analysis history with status and filtering or grouping.
  - Allow reopening an analysis without a raw select-only control.
- Out:
  - Team collaboration, sharing, or multi-user administration.

# Acceptance criteria
- Recent analyses are scannable by video, status, and recency.
- Creating a new analysis remains a short, focused flow.

# AC Traceability
- request-AC6 -> This backlog slice. Proof: Recent analyses are scannable by video, status, and recency.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_015_focused_english_language_claimlens_analysis_workspace`
- Architecture decision(s): (none yet)
- Request: `req_011_refine_the_claimlens_analysis_workspace_user_experience`
- Primary task(s): `task_012_orchestrate_the_claimlens_analysis_workspace_ux_refinement`

# AI Context
- Summary: Separate analysis creation from analysis history
- Keywords: scaffolded-backlog, separate analysis creation from analysis history, implementation-ready
- Use when: Implementing the scaffolded slice for Separate analysis creation from analysis history.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: Medium
- Rationale: Set by scaffold input or defaulted for grooming.

# Tasks
- `task_012_orchestrate_the_claimlens_analysis_workspace_ux_refinement`

# Notes
- Task `task_012_orchestrate_the_claimlens_analysis_workspace_ux_refinement` was finished via `logics-manager flow finish task` on 2026-07-24.
