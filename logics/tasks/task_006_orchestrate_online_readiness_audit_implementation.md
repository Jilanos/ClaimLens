## task_006_orchestrate_online_readiness_audit_implementation - Orchestrate Online Readiness Audit Implementation
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
- [x] 1. Confirm accepted and rejected audit findings are reflected in the request scope, including B1/B2 standby, F6 rejected, and report-language configuration for F1.
- [x] 2. Implement web mutation safety first: request-size limits, Content-Length validation, CSRF, and controlled errors.
- [x] 3. Add final report view/download routes with path traversal protection.
- [x] 4. Introduce report language configuration, metadata enrichment, and isolate out-of-scope YouTube channel scraping.
- [x] 5. Bound and ground LLM transcript analysis, then harden OpenAI/network failure handling.
- [x] 6. Improve source verification evidence retrieval, verdict vocabulary, confidence handling, and adapter error reporting.
- [x] 7. Add asynchronous job execution and progress UI for long-running actions.
- [x] 8. Refine process page accessibility, responsive behavior, transcript preview, source links, and run navigation.
- [x] 9. Harden SQLite concurrency, schema migrations, re-analysis idempotence, configuration loading, logging, Python version alignment, and local abuse controls.
- [x] 10. Update operator documentation and manual smoke-test guidance.
- [x] 11. Validate with ruff, pytest, compileall where applicable, logics-manager lint --require-status, and logics-manager audit before closeout.
- [x] 12. ADR 009 checkpoint: update affected Logics docs during each meaningful wave and leave the repo commit-ready; commit creation remains under operator control.
- [x] ADR 009 checkpoint: update affected Logics docs during each meaningful wave and leave the repo commit-ready.
- [x] Keep commit creation under operator control; do not force one commit per micro-step.
- [x] GATE: do not close until lint, audit, and scaffold validation pass.

# Backlog
- `item_030_harden_web_mutation_safety_controls`
- `item_031_serve_final_reports_in_the_web_ui`
- `item_032_configure_report_language_and_enrich_video_metadata`
- `item_033_bound_and_ground_llm_transcript_analysis`
- `item_034_improve_source_verification_evidence_quality`
- `item_035_build_asynchronous_process_ux`
- `item_036_refine_process_page_accessibility_and_run_navigation`
- `item_037_harden_sqlite_concurrency_and_schema_migrations`
- `item_038_stabilize_production_configuration_and_observability`
- `item_039_add_local_abuse_controls_for_costly_actions`
- `item_040_validate_and_document_online_readiness_closeout`

# Definition of Done (DoD)
- [x] Generated request, product, backlog, and task docs are present.
- [x] Context-pack handoff is available when requested.
- [x] Validation passes.
- [x] Meaningful waves followed ADR 009: affected docs updated and the repo left commit-ready without automatic commits.

# AC Traceability
- request-AC1 -> This task. Proof: `src/claimlens/web.py` validates `Content-Length`, enforces `config.web.max_request_bytes`, requires CSRF tokens for POST actions, and maps failures through controlled public messages.
- request-AC2 -> This task. Proof: `render_brief_page`, `/brief`, and `/brief/download` serve generated Markdown reports by run id and `_brief_path_for_run` rejects paths outside the configured briefs directory; `tests/test_analysis_briefs_web.py` covers rendering and traversal rejection.
- request-AC3 -> This task. Proof: `PipelineConfig.report_language`, `claimlens run-video --report-language`, web create-run language input, `pipeline.create_run`, and brief renderers propagate report language; config and report tests cover the flow.
- request-AC4 -> This task. Proof: `pipeline.create_run(..., fetch_metadata=True)` can enrich direct video runs through bounded YouTube oEmbed metadata, while `db.get_video` and brief renderers include locally available title/channel/date/duration/view metadata with fallbacks.
- request-AC5 -> This task. Proof: `analysis.py` bounds long transcripts, sets OpenAI `temperature=0`, parses grounded claim objects, and stores `claims.transcript_excerpt`; tests cover transcript bounds and excerpt persistence.
- request-AC6 -> This task. Proof: `claimlens transcribe` rejects channel URLs with a controlled message; tests cover the disabled channel-scraping path.
- request-AC7 -> This task. Proof: `verification.py` replaced snippet keyword polarity with explicit `assessment_polarity` metadata from the assessment boundary and conservative unclear fallback.
- request-AC8 -> This task. Proof: `PubMedAdapter` fetches PubMed abstracts via `efetch` and stores `evidence_text_source` metadata when falling back to title-only evidence.
- request-AC9 -> This task. Proof: verification confidence is no longer populated by hard-coded scores, adapter failures are logged, and claim rationales distinguish adapter errors from no-source outcomes.
- request-AC10 -> This task. Proof: `web.py` submits non-create actions to a local `ThreadPoolExecutor`; `db.jobs` persists queued/running/succeeded/failed state and the UI renders job progress.
- request-AC11 -> This task. Proof: `web.py` adds labels, controlled errors, bounded run list, source-video links, transcript preview, report links, and responsive-safe structure.
- request-AC12 -> This task. Proof: `db.connect` applies WAL and `busy_timeout`; schema v4 adds `jobs` and migration helpers cover new columns; `tests/test_db.py` covers pragmas and schema version.
- request-AC13 -> This task. Proof: `analysis.py` and `verification.py` catch HTTP/network/timeout/malformed response failures and web errors are sanitized before display; logging records failures.
- request-AC14 -> This task. Proof: `CLAIMLENS_CONFIG` and explicit config paths resolve relative TOML paths from the config file directory; tests cover non-cwd config loading.
- request-AC15 -> This task. Proof: `web.py` adds configurable local rate limiting for costly POST actions and README documents the future reverse-proxy dependency.
- request-AC16 -> This task. Proof: `db.create_job` rejects duplicate queued/running jobs for the same run/action and `upsert_analysis` prunes previous claims for the video before inserting the latest analysis.
- request-AC17 -> This task. Proof: `web.py`, `analysis.py`, and `verification.py` use structured logging without secrets; README/ROADMAP document deployment/runtime expectations.
- request-AC18 -> This task. Proof: `.venv/bin/ruff check .`, `.venv/bin/pytest`, `.venv/bin/python -m compileall -q src tests`, `logics-manager lint --require-status`, and `logics-manager audit` passed during closeout.

# Validation
- `.venv/bin/ruff check .` passed.
- `.venv/bin/pytest` passed with 42 tests.
- `.venv/bin/python -m compileall -q src tests` passed.
- `logics-manager lint --require-status` passed.
- `logics-manager audit` passed before closeout with only deferred-proof warnings while the task was not yet Done.
- .venv/bin/ruff check . passed; .venv/bin/pytest passed with 42 tests; .venv/bin/python -m compileall -q src tests passed; logics-manager lint --require-status passed; logics-manager audit passed with only pre-closeout deferred-proof warnings.
- Finish workflow executed on 2026-07-24.
- Linked backlog/request close verification passed.

# Report
- Implemented selected online-readiness audit findings and left B1/B2 as documented deployment standbys.
- Finished on 2026-07-24.
- Linked backlog item(s): `item_030_harden_web_mutation_safety_controls`, `item_031_serve_final_reports_in_the_web_ui`, `item_032_configure_report_language_and_enrich_video_metadata`, `item_033_bound_and_ground_llm_transcript_analysis`, `item_034_improve_source_verification_evidence_quality`, `item_035_build_asynchronous_process_ux`, `item_036_refine_process_page_accessibility_and_run_navigation`, `item_037_harden_sqlite_concurrency_and_schema_migrations`, `item_038_stabilize_production_configuration_and_observability`, `item_039_add_local_abuse_controls_for_costly_actions`, `item_040_validate_and_document_online_readiness_closeout`
- Related request(s): `req_005_online_readiness_audit_implementation`

# AI Context
- Summary: Orchestrate Online Readiness Audit Implementation
- Keywords: scaffolded-task, request-chain-scaffold, orchestration
- Use when: Coordinating implementation of a scaffolded request chain.
- Skip when: Working on one isolated sibling slice.

# Links
- Request: `req_005_online_readiness_audit_implementation`
- Product brief(s): `prod_006_claimlens_online_readiness_audit_implementation`
- Architecture decision(s): (none yet)
