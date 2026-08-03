## task_022_deliver_the_brief_first_analysis_workspace_and_validated_release - Deliver the brief-first analysis workspace and validated release
> From version: 1.0.0
> Schema version: 1.0
> Status: In progress
> Understanding: 90%
> Confidence: 90%
> Progress: 55%
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
- [ ] 5. Create the implementation commit.
- [ ] 6. Prepare the appropriate next SemVer version across all canonical version surfaces and create the version-preparation commit.
- [ ] 7. Push the version-preparation commit, wait for CI success on its exact SHA, then create and push an annotated vX.Y.Z tag and verify the tag-triggered release workflow.
- [ ] ADR 009 checkpoint: update affected Logics docs during each meaningful wave and leave the repo commit-ready.
- [ ] Keep commit creation under operator control; do not force one commit per micro-step.
- [ ] GATE: do not close until lint, audit, and scaffold validation pass.

# Backlog
- `item_093_make_the_completed_brief_full_page_and_recall_completed_analysis_details`
- `item_094_unify_the_new_analysis_launcher_and_expose_video_titles_in_history`
- `item_095_validate_and_release_the_brief_first_analysis_workspace`

# Definition of Done (DoD)
- [ ] Generated request, product, backlog, and task docs are present.
- [ ] Context-pack handoff is available when requested.
- [ ] Validation passes.
- [ ] Meaningful waves followed ADR 009: affected docs updated and the repo left commit-ready without automatic commits.

# AC Traceability
- request-AC1, request-AC2, request-AC3 -> `item_093_make_the_completed_brief_full_page_and_recall_completed_analysis_details`. Proof deferred to slice closeout.
- request-AC4, request-AC5 -> `item_094_unify_the_new_analysis_launcher_and_expose_video_titles_in_history`. Proof deferred to slice closeout.
- request-AC6, request-AC7 -> `item_095_validate_and_release_the_brief_first_analysis_workspace`. Proof deferred to slice closeout.

# Validation
- `pytest -q` (full suite): all tests pass.
- `ruff check .`: all checks passed.
- `logics-manager lint`: OK.
- `logics-manager audit`: OK (warnings only — companion-doc Mermaid diagrams and
  deferred AC task-traceability proof, both expected before task closeout).
- `logics-manager flow validate req_018_... item_093_... item_094_... item_095_... task_022_...`:
  0 findings.

# Report
- Implementation complete for item_093 (brief-first full-width workspace with an
  accessible `<details>` recall control for identity/status/Results) and item_094
  (fixed unclosed `.card-head` in the empty-landing launcher; moved video title into
  its own `.history-title` element in history rows). Focused tests added/updated in
  `tests/test_workspace_deliverables.py` and `tests/test_analysis_briefs_web.py`.
  Full test suite, Ruff, and Logics lint/audit/validate all pass.
- Remaining: implementation commit, SemVer version-preparation commit, push, CI
  verification, and annotated release tag (item_095).

# AI Context
- Summary: Deliver the brief-first analysis workspace and validated release
- Keywords: scaffolded-task, request-chain-scaffold, orchestration
- Use when: Coordinating implementation of a scaffolded request chain.
- Skip when: Working on one isolated sibling slice.

# Links
- Request: `req_018_prioritise_the_completed_analysis_brief_and_standardise_claimlens_delivery_releases`
- Product brief(s): `prod_022_brief_first_analysis_workspace_and_repeatable_release_delivery`
- Architecture decision(s): (none yet)
