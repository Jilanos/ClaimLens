## req_011_refine_the_claimlens_analysis_workspace_user_experience - Refine the ClaimLens analysis workspace user experience
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Complexity: High
> Theme: Operational UX refinement
> Reminder: Update status/understanding/confidence and linked backlog/task references when you edit this doc.

# Needs
- Refocus the Analysis page around the selected run, its current state, and the single next action a user should take.
- Remove duplicated progression information while preserving accessible operational detail.
- Reveal the pasted-transcript fallback only when subtitle extraction needs it.
- Make reports and verification outcomes easier to assess at a glance before users open Markdown.
- Separate creating an analysis from finding and revisiting prior analyses.
- Improve the mobile and keyboard experience without changing the application language.

# Context
- The current Process page combines creation, run selection, pipeline status, a five-step stepper, a step table, job history, outputs, and a manual transcript form into one vertical sequence.
- The application already has live job-state polling and semantic status messages, but its presentation still exposes several implementation-oriented labels such as clean_transcript and completed_with_warnings.
- The manual pasted-transcript form is always visible, although it is an exception path after captions cannot be obtained.
- Outputs are currently presented as links and raw counts rather than as a concise editorial or evidence summary.
- At narrow widths the five-step progression becomes a two-column grid, and table-heavy sections remain the primary representation.
- The product must remain fully English. This request does not introduce translation, locale selection, or French UI copy.

# Acceptance criteria
- A selected run has a clear primary workspace that identifies the video, current pipeline state, current provider/job message, and exactly one primary next action when user action is required.
- The primary workspace does not present the same progression state as competing stepper, table, and jobs views. Detailed execution history remains available without dominating the page.
- Internal action and status identifiers are rendered as concise English product labels, while technical details remain available in a dedicated diagnostic view.
- The pasted-transcript fallback is hidden during normal caption processing and becomes visible with a clear English explanation only after captions fail or are unavailable.
- Outputs contain a compact result summary that distinguishes a regular brief, evidence-backed verification, and an incomplete verification attempt, including claim/source counts and actionable warnings.
- Users can create a new analysis from a focused control and can browse, filter, reopen, and identify recent analyses separately from the active workspace.
- At mobile widths, pipeline progress uses a readable vertical or otherwise linear sequence; data tables have an accessible compact representation without horizontal workflow ambiguity.
- Keyboard focus, status text, and non-color indicators communicate state without relying on color alone.
- All newly introduced user-facing text is English. Ruff, pytest, browser or HTTP integration coverage for the affected workflow, Logics lint, and Logics audit pass before closeout.

# Definition of Ready (DoR)
- [x] Problem statement is explicit and user impact is clear.
- [x] Scope boundaries (in/out) are explicit.
- [x] Acceptance criteria are testable.
- [x] Dependencies and known risks are listed.

# Companion docs
- Product brief(s): `prod_015_focused_english_language_claimlens_analysis_workspace`
- Architecture decision(s): (none yet)

# References
- src/claimlens/web.py
- src/claimlens/briefs.py
- src/claimlens/verification.py
- tests/test_analysis_briefs_web.py
- tests/test_verification.py

# AI Context
- Summary: Refine the ClaimLens analysis workspace user experience
- Keywords: request-chain-scaffold, refine the claimlens analysis workspace user experience, development-ready
- Use when: You need to implement or review the scaffolded workflow for Refine the ClaimLens analysis workspace user experience.
- Skip when: The change is unrelated to this scaffolded request chain.

# Backlog
- `item_068_create_a_focused_active_analysis_workspace`
- `item_069_simplify_progress_and_diagnostic_presentation`
- `item_070_contextualize_transcript_recovery`
- `item_071_add_an_evidence_aware_results_summary`
- `item_072_separate_analysis_creation_from_analysis_history`
- `item_073_make_the_workflow_responsive_and_testable`
