## req_018_prioritise_the_completed_analysis_brief_and_standardise_claimlens_delivery_releases - Prioritise the completed analysis brief and standardise ClaimLens delivery releases
> From version: 1.0.0
> Schema version: 1.0
> Status: Draft
> Understanding: 90%
> Confidence: 85%
> Complexity: Medium
> Theme: Analysis workspace and release discipline
> Reminder: Update status/understanding/confidence and linked backlog/task references when you edit this doc.

# Needs
- When a brief exists, make it the full-width, primary reading surface of the Analyses page.
- Keep the completed-analysis identity, status, result summary, transcript, brief links, and source-verification outcome available but collapsed behind a persistent, accessible recall control placed beside the completed workspace.
- Keep the complete and warning terminal states truthful and distinguishable after they are collapsed.
- Make the new-analysis launcher use one stable, full-width layout whether the user lands on Analyses directly, arrives from another tab, or starts another analysis after a completed run.
- Give each Recent analyses row a clearly visible video-title line in addition to the video identifier and metadata.
- Ship the implementation using the repository release sequence: implementation commit, SemVer preparation, version commit, push, successful CI on that exact commit, then annotated version tag and release verification.

# Context
- The current completed workspace still allocates a left column to Analysis complete and Results, which prevents the embedded brief from owning the page.
- The existing completed view removed execution diagnostics entirely; the replacement must preserve read-only access rather than discard them.
- The non-collapsed launcher nests card-body inside card-head, producing the observed split layout; the collapsed launcher is the visual reference.
- Recent-analysis queries already join videos.title as video_title, so the history defect is presentation and regression coverage, not a schema change.
- Release-by-tag validates that the tagged commit is an ancestor of main, and the tag must therefore be created only after CI has passed for the pushed version-preparation commit.

# Acceptance criteria
- AC1 — For a run with a saved brief, the brief occupies the full content width of the Analyses workspace on desktop; the previous two-column completed layout is absent.
- AC2 — A visible, keyboard-operable recall control adjacent to the completed workspace exposes Analysis complete, the terminal status, Results, deliverable links, and source-verification outcome without changing or rerunning the analysis.
- AC3 — The recall control and its expanded content correctly represent both Complete and Complete with limits states, including accessible labels and sensible responsive behaviour.
- AC4 — The new-analysis form has the same full-width, aligned structure in the empty landing state and the Start another analysis state; no card-head/card-body nesting causes a split layout.
- AC5 — Each Recent analyses row shows the video identifier and its video title as independently visible text, with a graceful fallback only when title metadata is unavailable.
- AC6 — Focused rendering tests cover completed, warning, empty, and start-another states, and the complete test suite, Ruff, Logics lint, audit, and workflow validation pass.
- AC7 — The delivery ends with an implementation commit, a SemVer version-preparation commit, a push, a successful CI run for that exact commit, then an annotated vX.Y.Z tag and confirmation of the tag-triggered release workflow.

# Definition of Ready (DoR)
- [x] Problem statement is explicit and user impact is clear.
- [x] Scope boundaries (in/out) are explicit.
- [x] Acceptance criteria are testable.
- [x] Dependencies and known risks are listed.

# Companion docs
- Product brief(s): `prod_022_brief_first_analysis_workspace_and_repeatable_release_delivery`
- Architecture decision(s): (none yet)

# References
- src/claimlens/web.py
- tests/test_workspace_deliverables.py
- src/claimlens/__init__.py
- pyproject.toml
- .github/workflows/ci.yml
- .github/workflows/release.yml
- logics/instructions.md

# AI Context
- Summary: Prioritise the completed analysis brief and standardise ClaimLens delivery releases
- Keywords: request-chain-scaffold, prioritise the completed analysis brief and standardise claimlens delivery releases, development-ready
- Use when: You need to implement or review the scaffolded workflow for Prioritise the completed analysis brief and standardise ClaimLens delivery releases.
- Skip when: The change is unrelated to this scaffolded request chain.

# Backlog
- `item_093_make_the_completed_brief_full_page_and_recall_completed_analysis_details`
- `item_094_unify_the_new_analysis_launcher_and_expose_video_titles_in_history`
- `item_095_validate_and_release_the_brief_first_analysis_workspace`
