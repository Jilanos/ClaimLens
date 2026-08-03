## req_017_polish_the_claimlens_analysis_interface_and_completed_run_reading_view - Polish the ClaimLens analysis interface and completed-run reading view
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Complexity: Low
> Theme: Interface refinement
> Reminder: Update status/understanding/confidence and linked backlog/task references when you edit this doc.

# Needs
- Replace the analyses description with concise, fluent English.
- Rename the Options destination and page to API keys.
- Show each video's title in Recent analyses.
- Remove redundant copy and the Close analysis control.
- Use a compact completed-analysis view once the brief is available.
- Enlarge the mark artwork inside its existing square tile.

# Context
- Video metadata is already stored in the videos table.
- Completed runs remain readable through the brief and result links.
- The live-status client must not restore a removed control.

# Acceptance criteria
- The Analyses description is a single unconstrained desktop line and accurately describes the workflow in English.
- Options is labelled API keys in navigation, page heading, and document title.
- Recent analyses shows a video title after the video identifier.
- The redundant history and launcher copy, and the Close analysis button, are absent.
- When a saved brief is available, the active area hides operational diagnostics and presents a compact completion summary beside the brief.
- The 54px brand tile keeps its dimensions while its SVG artwork grows to 40px.

# Definition of Ready (DoR)
- [x] Problem statement is explicit and user impact is clear.
- [x] Scope boundaries (in/out) are explicit.
- [x] Acceptance criteria are testable.
- [x] Dependencies and known risks are listed.

# Companion docs
- Product brief(s): `prod_021_claimlens_analysis_interface_polish`
- Architecture decision(s): (none yet)

# References
- src/claimlens/web.py
- tests/test_workspace_deliverables.py

# AI Context
- Summary: Polish the ClaimLens analysis interface and completed-run reading view
- Keywords: request-chain-scaffold, polish the claimlens analysis interface and completed-run reading view, development-ready
- Use when: You need to implement or review the scaffolded workflow for Polish the ClaimLens analysis interface and completed-run reading view.
- Skip when: The change is unrelated to this scaffolded request chain.

# Backlog
- `item_091_refine_analysis_labels_history_metadata_and_completed_workspace_density`
- `item_092_increase_the_artwork_size_inside_the_claimlens_brand_tile`
