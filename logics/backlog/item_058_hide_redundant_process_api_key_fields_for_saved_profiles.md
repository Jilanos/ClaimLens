## item_058_hide_redundant_process_api_key_fields_for_saved_profiles - Hide redundant Process API key fields for saved profiles
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Low
> Theme: Authenticated workflow
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- Signed-in users are prompted for API keys even though the backend already resolves their saved encrypted keys.

# Scope
- In:
  - Render key fields conditionally by authenticated saved-key availability.
  - Preserve guest and missing-key manual entry flows.
- Out:
  - Changing key encryption, storage, or server fallback policy.

# Acceptance criteria
- Saved profile keys are used without showing redundant Process-page password inputs.
- No saved key value is included in HTML or JSON.

# AC Traceability
- request-AC4 -> This backlog slice. Proof: Saved profile keys are used without showing redundant Process-page password inputs.
- request-AC5 -> This backlog slice. Proof: No saved key value is included in HTML or JSON.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_013_live_claimlens_process_feedback_and_trustworthy_verification_results`
- Architecture decision(s): (none yet)
- Request: `req_009_make_process_state_live_and_verification_outcomes_actionable`
- Primary task(s): `task_010_orchestrate_live_process_feedback_and_verification_reliability_delivery`

# AI Context
- Summary: Hide redundant Process API key fields for saved profiles
- Keywords: scaffolded-backlog, hide redundant process api key fields for saved profiles, implementation-ready
- Use when: Implementing the scaffolded slice for Hide redundant Process API key fields for saved profiles.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: Medium
- Rationale: Set by scaffold input or defaulted for grooming.

# Tasks
- `task_010_orchestrate_live_process_feedback_and_verification_reliability_delivery`

# Notes
- Task `task_010_orchestrate_live_process_feedback_and_verification_reliability_delivery` was finished via `logics-manager flow finish task` on 2026-07-24.
