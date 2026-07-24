## item_070_contextualize_transcript_recovery - Contextualize transcript recovery
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Medium
> Theme: Exception handling
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- The manual transcript fallback is permanently visible despite being relevant only when subtitles cannot be retrieved.

# Scope
- In:
  - Show the fallback after caption failure or unavailability.
  - Provide clear English recovery copy and preserve the existing pasted transcript path.
  - Allow a user to return to normal workflow controls after recovery.
- Out:
  - Changing transcript providers or enabling generated captions.

# Acceptance criteria
- Normal runs do not display the pasted-transcript form.
- A failed captions run presents the fallback without requiring the user to infer the next recovery step.

# AC Traceability
- request-AC4 -> This backlog slice. Proof: Normal runs do not display the pasted-transcript form.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_015_focused_english_language_claimlens_analysis_workspace`
- Architecture decision(s): (none yet)
- Request: `req_011_refine_the_claimlens_analysis_workspace_user_experience`
- Primary task(s): `task_012_orchestrate_the_claimlens_analysis_workspace_ux_refinement`

# AI Context
- Summary: Contextualize transcript recovery
- Keywords: scaffolded-backlog, contextualize transcript recovery, implementation-ready
- Use when: Implementing the scaffolded slice for Contextualize transcript recovery.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.

# Tasks
- `task_012_orchestrate_the_claimlens_analysis_workspace_ux_refinement`

# Notes
- Task `task_012_orchestrate_the_claimlens_analysis_workspace_ux_refinement` was finished via `logics-manager flow finish task` on 2026-07-24.
