## item_096_make_completed_briefs_genuinely_full_page_by_default - Make completed briefs genuinely full page by default
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Medium
> Theme: Completed brief layout
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- The completed workspace uses a single-column grid, but the embedded report card still has a narrow max-width and desktop margin rules that keep it from occupying the available reading surface.

# Scope
- In:
  - Remove or override narrow completed-brief constraints so the completed brief card spans the workspace width.
  - Keep the brief text readable with a controlled measure inside the full-width card.
  - Preserve the accessible recall disclosure for completed run details and results.
- Out:
  - Pipeline, artifact generation, and authorization changes.
  - Standalone downloadable brief print layout changes unless directly necessary.

# Acceptance criteria
- AC1: Completed workspace HTML/CSS contains a completed-brief class or equivalent rule proving the report card itself is full width.
- AC2: The completed page has no permanent workspace-main column when a saved brief exists.
- AC3: Completed details and Results remain present inside a disclosure.

# AC Traceability
- request-AC1 -> This backlog slice. Proof: AC1: Completed workspace HTML/CSS contains a completed-brief class or equivalent rule proving the report card itself is full width.
- request-AC2 -> This backlog slice. Proof: AC2: The completed page has no permanent workspace-main column when a saved brief exists.
- request-AC5 -> This backlog slice. Proof: AC3: Completed details and Results remain present inside a disclosure.
- request-AC4 -> This backlog slice. Evidence needed: The README contains an extensive, screenshot-backed product narrative that explains the value of ClaimLens, the end-to-end workflow, outputs, source verification, privacy/key handling, and local/deployed usage.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_023_brief_first_claimlens_reading_and_adoption_documentation`
- Architecture decision(s): (none yet)
- Request: `req_019_correct_the_completed_brief_reading_surface_and_promote_claimlens_documentation`
- Primary task(s): `task_023_orchestrate_completed_brief_full_page_correction_history_title_emphasis_and_readme_promotion`

# AI Context
- Summary: Make completed briefs genuinely full page by default
- Keywords: scaffolded-backlog, make completed briefs genuinely full page by default, implementation-ready
- Use when: Implementing the scaffolded slice for Make completed briefs genuinely full page by default.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.

# Tasks
- `task_023_orchestrate_completed_brief_full_page_correction_history_title_emphasis_and_readme_promotion`

# Notes
- Task `task_023_orchestrate_completed_brief_full_page_correction_history_title_emphasis_and_readme_promotion` was finished via `logics-manager flow finish task` on 2026-08-03.
