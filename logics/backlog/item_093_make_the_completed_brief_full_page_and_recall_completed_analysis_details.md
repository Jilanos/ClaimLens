## item_093_make_the_completed_brief_full_page_and_recall_completed_analysis_details - Make the completed brief full-page and recall completed analysis details
> From version: 1.0.0
> Schema version: 1.0
> Status: Ready
> Understanding: 90%
> Confidence: 85%
> Progress: 0%
> Complexity: Medium
> Theme: Completed analysis workspace
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- A finished brief is rendered beside a permanent Analysis complete and Results column, while operational details were removed rather than being available on demand.

# Scope
- In:
  - Full-width embedded brief layout after a saved brief exists.
  - Accessible disclosure/recall control beside the completed workspace.
  - Completed and completed-with-warnings status, Results summary, deliverable links, and evidence outcome inside the recalled panel.
  - Responsive and regression tests.
- Out:
  - Pipeline changes, result recomputation, or destructive run-state changes.

# Acceptance criteria
- The saved brief is the sole primary column at desktop widths.
- Completed information is hidden by default but is fully recoverable by keyboard and pointer.
- Terminal statuses remain accurate and distinguish warnings from complete success.

# AC Traceability
- request-AC1 -> This backlog slice. Proof: The saved brief is the sole primary column at desktop widths.
- request-AC2 -> This backlog slice. Proof: Completed information is hidden by default but is fully recoverable by keyboard and pointer.
- request-AC3 -> This backlog slice. Proof: Terminal statuses remain accurate and distinguish warnings from complete success.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_022_brief_first_analysis_workspace_and_repeatable_release_delivery`
- Architecture decision(s): (none yet)
- Request: `req_018_prioritise_the_completed_analysis_brief_and_standardise_claimlens_delivery_releases`
- Primary task(s): `task_022_deliver_the_brief_first_analysis_workspace_and_validated_release`

# AI Context
- Summary: Make the completed brief full-page and recall completed analysis details
- Keywords: scaffolded-backlog, make the completed brief full-page and recall completed analysis details, implementation-ready
- Use when: Implementing the scaffolded slice for Make the completed brief full-page and recall completed analysis details.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High — the main analysis reading experience is currently constrained by secondary panels.
- Rationale: Set by scaffold input or defaulted for grooming.
