## task_021_deliver_the_claimlens_analysis_interface_polish - Deliver the ClaimLens analysis interface polish
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Medium
> Theme: Implementation delivery
> Reminder: Update status/understanding/confidence/progress and linked request/backlog references when you edit this doc.
> Owner: codex

# Context
- Orchestrate the scaffolded request chain and keep sibling implementation slices linked.

# Plan
- [x] 1. Inspect the existing page, history, navigation, and brand-mark renderers.
- [x] 2. Implement the requested copy, title metadata, API keys naming, and compact completed view.
- [x] 3. Remove the close-control live region so polling cannot restore the retired button.
- [x] 4. Enlarge the mark artwork without changing the tile.
- [x] 5. Run targeted UI tests, the full test suite, lint, and Logics validation.
- [x] ADR 009 checkpoint: update affected Logics docs during each meaningful wave and leave the repo commit-ready.
- [x] Keep commit creation under operator control; do not force one commit per micro-step.
- [x] GATE: do not close until lint, audit, and scaffold validation pass.

# Backlog
- `item_091_refine_analysis_labels_history_metadata_and_completed_workspace_density`
- `item_092_increase_the_artwork_size_inside_the_claimlens_brand_tile`

# Definition of Done (DoD)
- [x] Generated request, product, backlog, and task docs are present.
- [x] Context-pack handoff is available when requested.
- [x] Validation passes.
- [x] Meaningful waves followed ADR 009: affected docs updated and the repo left commit-ready without automatic commits.

# AC Traceability
- request-AC1, request-AC2, request-AC3, request-AC4, request-AC5 -> `item_091_refine_analysis_labels_history_metadata_and_completed_workspace_density`. Proof deferred to slice closeout.
- request-AC6 -> `item_092_increase_the_artwork_size_inside_the_claimlens_brand_tile`. Proof deferred to slice closeout.

# Validation
- (no validation recorded yet)
- .venv/bin/pytest: 206 passed; .venv/bin/ruff check src tests: passed; logics-manager lint: OK; selected flow validation: OK on 2026-08-03.
- Finish workflow executed on 2026-08-03.
- Linked backlog/request close verification passed.

# Report
- Updated the analyses copy, renamed Options to API keys, and removed redundant launcher/history copy.
- History rows now join their video metadata and display the video title after the video identifier.
- The live region and payload that could render Close analysis were removed; completed runs with a saved brief now use a compact summary beside that brief.
- The brand tile remains 54px square while its SVG artwork grows from 31px to 40px.
- Finished on 2026-08-03.
- Linked backlog item(s): `item_091_refine_analysis_labels_history_metadata_and_completed_workspace_density`, `item_092_increase_the_artwork_size_inside_the_claimlens_brand_tile`
- Related request(s): `req_017_polish_the_claimlens_analysis_interface_and_completed_run_reading_view`

# AI Context
- Summary: Deliver the ClaimLens analysis interface polish
- Keywords: scaffolded-task, request-chain-scaffold, orchestration
- Use when: Coordinating implementation of a scaffolded request chain.
- Skip when: Working on one isolated sibling slice.

# Links
- Request: `req_017_polish_the_claimlens_analysis_interface_and_completed_run_reading_view`
- Product brief(s): `prod_021_claimlens_analysis_interface_polish`
- Architecture decision(s): (none yet)
