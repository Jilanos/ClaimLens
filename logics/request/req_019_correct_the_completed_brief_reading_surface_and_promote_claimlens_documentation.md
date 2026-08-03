## req_019_correct_the_completed_brief_reading_surface_and_promote_claimlens_documentation - Correct the completed brief reading surface and promote ClaimLens documentation
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Complexity: Medium
> Theme: Completed analysis reading experience
> Reminder: Update status/understanding/confidence and linked backlog/task references when you edit this doc.

# Needs
- Make completed briefs full-page by default in the Analyses workspace when a saved brief exists.
- Render the video title on the same visible line as the video code in old/recent analyses, after a separator, and make the title visually dominant.
- Document ClaimLens extensively in the README with screenshots and explanations that show why the tool is useful and make readers want to use it.

# Context
- The previous brief-first delivery was marked complete, but the supplied screenshot shows the completed brief still constrained to a narrow left-aligned report card instead of using the page width.
- Recent analyses already carries video title metadata, but the title is currently rendered on a secondary line and does not attract attention before the video identifier.
- The README currently documents the tool accurately but does not sell the workflow with screenshots, reader-focused benefits, or a usage narrative.

# Acceptance criteria
- AC1: A completed run with a saved brief renders the brief as the dominant full-width reading surface by default, without a narrow report max-width or a competing permanent side column.
- AC2: Completed run details, status, deliverable links, transcript access, and source-verification outcome remain recoverable through an accessible disclosure and are not removed.
- AC3: Each Recent analyses row displays video_id and video_title on the same primary line using a clear separator, with the video title emphasized more strongly than the identifier and with a graceful fallback when no title exists.
- AC4: The README contains an extensive, screenshot-backed product narrative that explains the value of ClaimLens, the end-to-end workflow, outputs, source verification, privacy/key handling, and local/deployed usage.
- AC5: Focused rendering tests prove the full-page brief layout and title presentation, and the normal quality gates pass or any remaining limitation is explicitly recorded.

# AC Traceability
- request-AC1 -> `task_023_orchestrate_completed_brief_full_page_correction_history_title_emphasis_and_readme_promotion`. Proof: `src/claimlens/web.py` renders completed briefs with `card report report-complete`, and CSS sets `.workspace.complete .report-complete` to `width:100%; max-width:none; margin:0;`. Covered by `tests/test_analysis_briefs_web.py::test_the_completed_workspace_gives_the_brief_the_full_width`.
- request-AC2 -> `task_023_orchestrate_completed_brief_full_page_correction_history_title_emphasis_and_readme_promotion`. Proof: the completed workspace keeps the `recall` disclosure with status, video identity, `Results`, transcript links, brief links, and source-verification outcome. Covered by `tests/test_analysis_briefs_web.py::test_the_completed_workspace_gives_the_brief_the_full_width`.
- request-AC3 -> `task_023_orchestrate_completed_brief_full_page_correction_history_title_emphasis_and_readme_promotion`. Proof: `src/claimlens/web.py` renders distinct titles as `.history-code : .history-title` inside one `.history-primary` line, with fallback to one emphasized title when no distinct metadata exists. Covered by `tests/test_workspace_deliverables.py::test_recent_analyses_shows_a_distinct_title_independently_of_the_identifier` and fallback history tests.
- request-AC4 -> `task_023_orchestrate_completed_brief_full_page_correction_history_title_emphasis_and_readme_promotion`. Proof: `README.md` now includes a product value proposition, use-case narrative, screenshot section, product tour, outputs, trust model, local-first shape, and screenshot refresh targets; `docs/screenshots/completed-brief-before-fix.png` is checked in as the supplied visual reference.
- request-AC5 -> `task_023_orchestrate_completed_brief_full_page_correction_history_title_emphasis_and_readme_promotion`. Proof: `PYTHONPATH=src pytest tests/test_analysis_briefs_web.py tests/test_workspace_deliverables.py` passed with 74 tests, `PYTHONPATH=src pytest` passed with 211 tests, `logics-manager lint` passed, `logics-manager audit` passed with non-blocking warnings, and `logics-manager flow validate task_023_orchestrate_completed_brief_full_page_correction_history_title_emphasis_and_readme_promotion` passed with 0 findings. Ruff was attempted but unavailable because neither `ruff` nor `python3 -m ruff` is installed.

# Definition of Ready (DoR)
- [x] Problem statement is explicit and user impact is clear.
- [x] Scope boundaries (in/out) are explicit.
- [x] Acceptance criteria are testable.
- [x] Dependencies and known risks are listed.

# Companion docs
- Product brief(s): `prod_023_brief_first_claimlens_reading_and_adoption_documentation`
- Architecture decision(s): (none yet)

# References
- User screenshot: /home/paul/dev/WORK/perso/not full page.png
- src/claimlens/web.py
- tests/test_analysis_briefs_web.py
- tests/test_workspace_deliverables.py
- README.md

# AI Context
- Summary: Correct the completed brief reading surface and promote ClaimLens documentation
- Keywords: request-chain-scaffold, correct the completed brief reading surface and promote claimlens documentation, development-ready
- Use when: You need to implement or review the scaffolded workflow for Correct the completed brief reading surface and promote ClaimLens documentation.
- Skip when: The change is unrelated to this scaffolded request chain.

# Backlog
- `item_096_make_completed_briefs_genuinely_full_page_by_default`
- `item_097_make_recent_analysis_rows_title_first_and_same_line`
- `item_098_rewrite_readme_as_a_screenshot_backed_product_guide`
