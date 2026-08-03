## task_022_deliver_the_brief_first_analysis_workspace_and_validated_release - Deliver the brief-first analysis workspace and validated release
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 95%
> Progress: 100%
> Complexity: Medium
> Theme: Implementation delivery
> Reminder: Update status/understanding/confidence/progress and linked request/backlog references when you edit this doc.

# Context
- Orchestrate the scaffolded request chain and keep sibling implementation slices linked.

# Plan
- [x] 1. Inspect the completed workspace renderer, CSS breakpoints, launcher markup, history renderer, and existing rendering tests.
- [x] 2. Implement the full-width brief and the adjacent accessible recall control, preserving truthful terminal state and results content.
- [x] 3. Repair the direct new-analysis card structure and align history title presentation.
- [x] 4. Add focused tests, run the full quality and Logics gates, and record their evidence.
- [x] 5. Create the implementation commit.
- [x] 6. Prepare the appropriate next SemVer version across all canonical version surfaces and create the version-preparation commit.
- [x] 7. Push the version-preparation commit, wait for CI success on its exact SHA, then create and push an annotated vX.Y.Z tag and verify the tag-triggered release workflow.
- [x] ADR 009 checkpoint: update affected Logics docs during each meaningful wave and leave the repo commit-ready.
- [x] Keep commit creation under operator control; do not force one commit per micro-step.
- [x] GATE: do not close until lint, audit, and scaffold validation pass.

# Backlog
- `item_093_make_the_completed_brief_full_page_and_recall_completed_analysis_details`
- `item_094_unify_the_new_analysis_launcher_and_expose_video_titles_in_history`
- `item_095_validate_and_release_the_brief_first_analysis_workspace`

# Definition of Done (DoD)
- [x] Generated request, product, backlog, and task docs are present.
- [x] Context-pack handoff is available when requested.
- [x] Validation passes.
- [x] Meaningful waves followed ADR 009: affected docs updated and the repo left commit-ready without automatic commits.

# AC Traceability
- request-AC1, request-AC2, request-AC3 -> `item_093_make_the_completed_brief_full_page_and_recall_completed_analysis_details`. Proof: `src/claimlens/web.py` `_active_workspace()` completed branch renders the brief as the sole `.workspace-brief` column with `.workspace.complete { grid-template-columns:minmax(0,1fr); }` at desktop, and the identity/status/Results are collapsed behind an accessible `<details class="recall">` control; covered by `test_the_completed_workspace_gives_the_brief_the_full_width` in `tests/test_analysis_briefs_web.py`.
- request-AC4, request-AC5 -> `item_094_unify_the_new_analysis_launcher_and_expose_video_titles_in_history`. Proof: `_create_card()` closes `.card-head` before `.card-body` in the empty-landing state, matching the collapsed-launcher form; covered by `test_the_empty_landing_launcher_has_no_isolated_heading_column` and `test_start_another_analysis_reuses_the_same_full_width_form`. History rows show the title in an independent `.history-title` element; covered by `test_recent_analyses_shows_the_video_title_after_its_identifier`, `test_recent_analyses_shows_a_distinct_title_independently_of_the_identifier`, and `test_recent_analyses_falls_back_to_the_identifier_without_title_metadata` in `tests/test_workspace_deliverables.py`.
- request-AC6, request-AC7 -> `item_095_validate_and_release_the_brief_first_analysis_workspace`. Proof: full `pytest` suite, `ruff check .`, and `logics-manager` lint/audit/validate all passed (see Validation section); implementation commit `0c47618`, version-preparation commit `574bb6f` (v1.7.0) pushed to `main`, CI green on that exact SHA (run 30817251353), annotated tag `v1.7.0` pushed, and the tag-triggered "Release by tag" workflow succeeded (run 30817334687).

# Validation
- `pytest -q` (full suite): all tests pass.
- `ruff check .`: all checks passed.
- `logics-manager lint`: OK.
- `logics-manager audit`: OK (warnings only — companion-doc Mermaid diagrams and
- pytest full suite pass; ruff clean; logics lint/audit/validate clean; CI green on 574bb6f; v1.7.0 tag released
- Finish workflow executed on 2026-08-03.
- Linked backlog/request close verification passed.
  deferred AC task-traceability proof, both expected before task closeout).
- `logics-manager flow validate req_018_... item_093_... item_094_... item_095_... task_022_...`:
  0 findings.
- CI succeeded on the exact version-preparation commit `574bb6f` (run 30817251353)
  before tagging.
- `v1.7.0` annotated tag pushed from `574bb6f`; "Release by tag" workflow (run
  30817334687) succeeded; GitHub release `v1.7.0` confirmed via
  `gh release view v1.7.0`.

# Report
- Implementation complete for item_093 (brief-first full-width workspace with an
- Finished on 2026-08-03.
- Linked backlog item(s): `item_093_make_the_completed_brief_full_page_and_recall_completed_analysis_details`, `item_094_unify_the_new_analysis_launcher_and_expose_video_titles_in_history`, `item_095_validate_and_release_the_brief_first_analysis_workspace`
- Related request(s): `req_018_prioritise_the_completed_analysis_brief_and_standardise_claimlens_delivery_releases`
  accessible `<details>` recall control for identity/status/Results) and item_094
  (fixed unclosed `.card-head` in the empty-landing launcher; moved video title into
  its own `.history-title` element in history rows). Focused tests added/updated in
  `tests/test_workspace_deliverables.py` and `tests/test_analysis_briefs_web.py`.
  Full test suite, Ruff, and Logics lint/audit/validate all pass.
- item_095 delivered: implementation commit `0c47618`, version-preparation commit
  `574bb6f` (ClaimLens 1.7.0), pushed to `main`, CI green on that exact SHA, annotated
  tag `v1.7.0` pushed, and the tag-triggered release workflow verified successful.
- Remaining: close out the request/backlog/task docs with AC traceability proof.

# AI Context
- Summary: Deliver the brief-first analysis workspace and validated release
- Keywords: scaffolded-task, request-chain-scaffold, orchestration
- Use when: Coordinating implementation of a scaffolded request chain.
- Skip when: Working on one isolated sibling slice.

# Links
- Request: `req_018_prioritise_the_completed_analysis_brief_and_standardise_claimlens_delivery_releases`
- Product brief(s): `prod_022_brief_first_analysis_workspace_and_repeatable_release_delivery`
- Architecture decision(s): (none yet)
