## task_004_orchestrate_single_video_local_first_mvp - Orchestrate Single Video Local First MVP
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Medium
> Theme: Implementation delivery
> Reminder: Update status/understanding/confidence/progress and linked request/backlog references when you edit this doc.

# Context
- Orchestrate the scaffolded request chain and keep sibling implementation slices linked.

# Plan
- [ ] 1. Replace channel ingestion assumptions with the single-video run model.
- [ ] 2. Harden mandatory subtitle extraction and add cleaned transcript output.
- [ ] 3. Implement the OpenAI analysis boundary and structured analysis storage.
- [ ] 4. Render direct Markdown briefs labeled as not advanced-source-verified.
- [ ] 5. Document optional advanced source verification interfaces without enabling them by default.
- [ ] 6. Build the local HTML process page with step status, failure details, and next-step controls.
- [ ] 7. Validate with mocked unit tests plus a documented manual smoke test.
- [ ] 8. Update affected Logics docs during meaningful waves and leave the repo commit-ready.
- [ ] ADR 009 checkpoint: update affected Logics docs during each meaningful wave and leave the repo commit-ready.
- [ ] Keep commit creation under operator control; do not force one commit per micro-step.
- [ ] GATE: do not close until lint, audit, and scaffold validation pass.

# Backlog
- `item_014_implement_single_video_run_model_and_url_input`
- `item_015_make_subtitle_extraction_mandatory_and_add_transcript_cleanup`
- `item_016_add_openai_llm_analysis_for_cleaned_transcripts`
- `item_017_generate_direct_markdown_brief_from_llm_analysis`
- `item_018_design_optional_advanced_source_verification_mode`
- `item_019_build_local_html_process_page`
- `item_020_add_end_to_end_local_mvp_validation`

# Definition of Done (DoD)
- [x] Generated request, product, backlog, and task docs are present.
- [x] Context-pack handoff is available when requested.
- [x] Validation passes.
- [x] Meaningful waves followed ADR 009: affected docs updated and the repo left commit-ready without automatic commits.

# AC Traceability
- request-AC1 -> `item_014_implement_single_video_run_model_and_url_input`, `item_016_add_openai_llm_analysis_for_cleaned_transcripts`. Proof deferred until implementation closeout.
- request-AC2 -> `item_014_implement_single_video_run_model_and_url_input`. Proof deferred until implementation closeout.
- request-AC3 -> `item_015_make_subtitle_extraction_mandatory_and_add_transcript_cleanup`. Proof deferred until implementation closeout.
- request-AC4 -> `item_015_make_subtitle_extraction_mandatory_and_add_transcript_cleanup`. Proof deferred until implementation closeout.
- request-AC5 -> `item_016_add_openai_llm_analysis_for_cleaned_transcripts`. Proof deferred until implementation closeout.
- request-AC6 -> `item_017_generate_direct_markdown_brief_from_llm_analysis`. Proof deferred until implementation closeout.
- request-AC7 -> `item_018_design_optional_advanced_source_verification_mode`. Proof deferred until implementation closeout.
- request-AC8 -> `item_019_build_local_html_process_page`. Proof deferred until implementation closeout.
- request-AC9 -> `item_014_implement_single_video_run_model_and_url_input`, `item_017_generate_direct_markdown_brief_from_llm_analysis`, `item_019_build_local_html_process_page`. Proof deferred until implementation closeout.
- request-AC10 -> `item_015_make_subtitle_extraction_mandatory_and_add_transcript_cleanup`, `item_016_add_openai_llm_analysis_for_cleaned_transcripts`, `item_017_generate_direct_markdown_brief_from_llm_analysis`, `item_019_build_local_html_process_page`, `item_020_add_end_to_end_local_mvp_validation`. Proof deferred until implementation closeout.
- request-AC1 -> This task. Proof: `claimlens run-video <youtube-url>` creates a one-video run and accepts `OPENAI_API_KEY` or `--openai-api-key`; tests cover missing-key stop behavior without persisting secrets.
- request-AC2 -> This task. Proof: `parse_youtube_video_url` accepts watch, short, youtu.be, and embed URLs, rejects ambiguous channel URLs, and `pipeline_runs`/`run_steps` persist run state in SQLite.
- request-AC3 -> This task. Proof: `extract_required_subtitles` marks captions and run status failed with a user-readable no-subtitles message when transcript fetch fails; deterministic tests assert the persisted failure.
- request-AC4 -> This task. Proof: `clean_run_transcript` writes timestamp-free cleaned transcript text to configured output paths while `transcript_segments` preserve raw subtitle segments; deterministic tests assert both.
- request-AC5 -> This task. Proof: `analysis.OpenAIAnalysisClient` and `AnalysisClient` protocol define the OpenAI boundary; mocked tests store summary, key points, notable claims, caveats, and editorial notes.
- request-AC6 -> This task. Proof: `briefs.generate_brief` renders `outputs/briefs/<video_id>.md` from stored analysis and labels claim verdicts as not checked without requiring source retrieval.
- request-AC7 -> This task. Proof: `adr_001_single_video_local_first_pipeline` defines optional advanced source verification after analysis, and `advanced_source_verification = false` keeps it disabled by default.
- request-AC8 -> This task. Proof: `web.render_process_page` and `claimlens serve` provide a local HTML process page with run creation/loading, step statuses, failure causes, outputs, and next-step POST controls.
- request-AC9 -> This task. Proof: database, transcript, brief, host, and port paths are configurable; OpenAI keys are runtime inputs only and are not written to SQLite outputs or generated briefs.
- request-AC10 -> This task. Proof: `PYTHONPATH=src pytest` passed 27 tests covering URL parsing, subtitle failures, cleanup, mocked OpenAI analysis, brief rendering, and process-page rendering without live network calls.

# Validation
- Run `python3 -m logics_manager lint --require-status`.
- Run scaffold command tests.
- Finish workflow executed on 2026-07-23.
- Linked backlog/request close verification passed.

# Report
- Implementation complete.
- Finished on 2026-07-23.
- Linked backlog item(s): `item_014_implement_single_video_run_model_and_url_input`, `item_015_make_subtitle_extraction_mandatory_and_add_transcript_cleanup`, `item_016_add_openai_llm_analysis_for_cleaned_transcripts`, `item_017_generate_direct_markdown_brief_from_llm_analysis`, `item_018_design_optional_advanced_source_verification_mode`, `item_019_build_local_html_process_page`, `item_020_add_end_to_end_local_mvp_validation`
- Related request(s): `req_003_mvp_single_video_local_first_pipeline`

# AI Context
- Summary: Orchestrate Single Video Local First MVP
- Keywords: scaffolded-task, request-chain-scaffold, orchestration
- Use when: Coordinating implementation of a scaffolded request chain.
- Skip when: Working on one isolated sibling slice.

# Links
- Request: `req_003_mvp_single_video_local_first_pipeline`
- Product brief(s): `prod_004_claimlens_single_video_local_first_mvp`
- Architecture decision(s): `adr_001_single_video_local_first_pipeline`
