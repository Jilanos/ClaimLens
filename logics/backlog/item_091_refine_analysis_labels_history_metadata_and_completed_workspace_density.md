## item_091_refine_analysis_labels_history_metadata_and_completed_workspace_density - Refine analysis labels, history metadata, and completed workspace density
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Low
> Theme: Interface refinement
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- The interface uses vague labels, repeats low-value copy, and leaves a full operational workspace open after a brief is ready.

# Scope
- In:
  - Analyses, Recent analyses, API keys, and completed-workspace rendering.
  - Tests for the visible text and compact completed state.
- Out:
  - Pipeline execution and data model changes beyond selecting already stored video titles.

# Acceptance criteria
- All requested labels and copy are updated.
- History rows display title metadata.
- A persisted brief selects the compact completed view without diagnostic controls.

# AC Traceability
- request-AC1 -> This backlog slice. Proof: All requested labels and copy are updated.
- request-AC2 -> This backlog slice. Proof: History rows display title metadata.
- request-AC3 -> This backlog slice. Proof: A persisted brief selects the compact completed view without diagnostic controls.
- request-AC4 -> This backlog slice. Proof: A persisted brief selects the compact completed view without diagnostic controls.
- request-AC5 -> This backlog slice. Proof: A persisted brief selects the compact completed view without diagnostic controls.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_021_claimlens_analysis_interface_polish`
- Architecture decision(s): (none yet)
- Request: `req_017_polish_the_claimlens_analysis_interface_and_completed_run_reading_view`
- Primary task(s): `task_021_deliver_the_claimlens_analysis_interface_polish`

# AI Context
- Summary: Refine analysis labels, history metadata, and completed workspace density
- Keywords: scaffolded-backlog, refine analysis labels, history metadata, and completed workspace density, implementation-ready
- Use when: Implementing the scaffolded slice for Refine analysis labels, history metadata, and completed workspace density.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High — directly improves the primary analysis and review workflow.
- Rationale: Set by scaffold input or defaulted for grooming.

# Tasks
- `task_021_deliver_the_claimlens_analysis_interface_polish`

# Notes
- Task `task_021_deliver_the_claimlens_analysis_interface_polish` was finished via `logics-manager flow finish task` on 2026-08-03.
