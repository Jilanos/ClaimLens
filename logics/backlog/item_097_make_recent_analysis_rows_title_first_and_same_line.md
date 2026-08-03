## item_097_make_recent_analysis_rows_title_first_and_same_line - Make recent analysis rows title-first and same-line
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Low
> Theme: History scanability
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- The video title is available but displayed as secondary text below the identifier, so old analyses are still scanned by code rather than by meaningful title.

# Scope
- In:
  - Render video_id and video_title on the same primary line with a clear separator.
  - Emphasize the title as the dominant text while keeping the video_id available.
  - Keep status badges, close/reopen actions, timestamps, and filtering unchanged.
- Out:
  - Metadata ingestion or schema changes.
  - History filtering and retention changes.

# Acceptance criteria
- AC1: Rows with a title render a same-line video code plus separator plus emphasized title.
- AC2: Rows without a distinct title render a sensible fallback without duplicated noisy text.
- AC3: Regression tests cover both title and fallback rendering.

# AC Traceability
- request-AC3 -> This backlog slice. Proof: AC1: Rows with a title render a same-line video code plus separator plus emphasized title.
- request-AC5 -> This backlog slice. Proof: AC2: Rows without a distinct title render a sensible fallback without duplicated noisy text.
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
- Summary: Make recent analysis rows title-first and same-line
- Keywords: scaffolded-backlog, make recent analysis rows title-first and same-line, implementation-ready
- Use when: Implementing the scaffolded slice for Make recent analysis rows title-first and same-line.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.

# Tasks
- `task_023_orchestrate_completed_brief_full_page_correction_history_title_emphasis_and_readme_promotion`

# Notes
- Task `task_023_orchestrate_completed_brief_full_page_correction_history_title_emphasis_and_readme_promotion` was finished via `logics-manager flow finish task` on 2026-08-03.
