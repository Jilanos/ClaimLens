## task_004_orchestrate_single_video_local_first_mvp - Orchestrate Single Video Local First MVP
> From version: 1.0.0
> Schema version: 1.0
> Status: Ready
> Understanding: 90%
> Confidence: 85%
> Progress: 0%
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
- [ ] Generated request, product, backlog, and task docs are present.
- [ ] Context-pack handoff is available when requested.
- [ ] Validation passes.
- [ ] Meaningful waves followed ADR 009: affected docs updated and the repo left commit-ready without automatic commits.

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

# Validation
- Run `python3 -m logics_manager lint --require-status`.
- Run scaffold command tests.

# Report
- Implementation complete.

# AI Context
- Summary: Orchestrate Single Video Local First MVP
- Keywords: scaffolded-task, request-chain-scaffold, orchestration
- Use when: Coordinating implementation of a scaffolded request chain.
- Skip when: Working on one isolated sibling slice.

# Links
- Request: `req_003_mvp_single_video_local_first_pipeline`
- Product brief(s): `prod_004_claimlens_single_video_local_first_mvp`
- Architecture decision(s): `adr_001_single_video_local_first_pipeline`
