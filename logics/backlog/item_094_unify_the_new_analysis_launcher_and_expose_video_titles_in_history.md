## item_094_unify_the_new_analysis_launcher_and_expose_video_titles_in_history - Unify the new-analysis launcher and expose video titles in history
> From version: 1.0.0
> Schema version: 1.0
> Status: Ready
> Understanding: 90%
> Confidence: 85%
> Progress: 0%
> Complexity: Low
> Theme: Analysis navigation
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- The direct landing launcher has malformed card structure and the video title in history is visually easy to miss.

# Scope
- In:
  - Correct card markup and reuse the full-width launcher form layout in both entry states.
  - History typography/layout that clearly separates video ID, title, analysis number, timestamp, and status.
  - Fallback rendering tests for absent title metadata.
- Out:
  - Changing history retention, ownership, filtering semantics, or video metadata persistence.

# Acceptance criteria
- Both new-analysis entry states have matching form geometry and no isolated heading column.
- The title is independently readable in every history row when present.

# AC Traceability
- request-AC4 -> This backlog slice. Proof: Both new-analysis entry states have matching form geometry and no isolated heading column.
- request-AC5 -> This backlog slice. Proof: The title is independently readable in every history row when present.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_022_brief_first_analysis_workspace_and_repeatable_release_delivery`
- Architecture decision(s): (none yet)
- Request: `req_018_prioritise_the_completed_analysis_brief_and_standardise_claimlens_delivery_releases`
- Primary task(s): `task_022_deliver_the_brief_first_analysis_workspace_and_validated_release`

# AI Context
- Summary: Unify the new-analysis launcher and expose video titles in history
- Keywords: scaffolded-backlog, unify the new-analysis launcher and expose video titles in history, implementation-ready
- Use when: Implementing the scaffolded slice for Unify the new-analysis launcher and expose video titles in history.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High — starting a run and locating a past one are primary navigation actions.
- Rationale: Set by scaffold input or defaulted for grooming.
