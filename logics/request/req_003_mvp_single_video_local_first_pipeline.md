## req_003_mvp_single_video_local_first_pipeline - MVP: Single Video Local First Pipeline
> From version: 1.0.0
> Schema version: 1.0
> Status: Draft
> Understanding: 90%
> Confidence: 85%
> Complexity: High
> Theme: Local-first MVP
> Reminder: Update status/understanding/confidence and linked backlog/task references when you edit this doc.

# Needs
- Accept a single YouTube video URL as the MVP input instead of monitoring channels.
- Require existing YouTube subtitles; if subtitles are unavailable, stop the pipeline and explain the failure cause.
- Clean subtitle text by removing timestamps and obvious transcript noise before LLM analysis.
- Use an OpenAI API key entered at the start of the run for summary and brief generation.
- Skip advanced source retrieval and claim verdicts in the base MVP, while designing an optional advanced source verification mode for later.
- Provide a local HTML process page that documents each step, failures, and lets the user launch the next eligible step.

# Context
- The previous roadmap centered on channel ingestion and candidate selection; the refined MVP removes those stages.
- The repository already has SQLite schema, CLI scaffolding, and a working subtitle extraction path for YouTube videos with captions.
- The target deployment model is local-first, with a future VPS-hosted local web UI or service.
- The MVP should be review-first and should fail clearly instead of fabricating missing transcript or source-check data.

# Acceptance criteria
- AC1: A user can start a run with exactly one YouTube video URL and an OpenAI API key provided interactively or through environment/config.
- AC2: The pipeline validates that the URL resolves to a single video ID and records a pipeline run state in SQLite.
- AC3: Subtitle extraction succeeds only when YouTube captions are available; otherwise the run stops with a persisted, user-readable failure cause.
- AC4: Transcript cleanup stores a timestamp-free, normalized text artifact suitable for LLM input while preserving the raw segmented transcript in SQLite.
- AC5: The LLM step uses OpenAI to produce a concise summary, key points, notable claims, caveats, and editorial notes from the cleaned transcript.
- AC6: The base MVP can generate a reviewable Markdown brief directly after LLM analysis without requiring source retrieval or verdict assessment.
- AC7: The architecture defines an optional advanced source verification mode that can later add source retrieval and claim assessment without blocking the base MVP.
- AC8: A local HTML process page shows the current run, step statuses, failure causes, outputs, and action controls for launching the next eligible step.
- AC9: The implementation remains local-first and VPS-ready: no hardcoded localhost-only assumptions, file paths are configurable, and secrets are not persisted in generated outputs.
- AC10: Tests cover URL parsing, subtitle-unavailable failure, transcript cleanup, OpenAI client boundaries, brief rendering, and HTML process-state rendering without live network calls.

# Definition of Ready (DoR)
- [x] Problem statement is explicit and user impact is clear.
- [x] Scope boundaries (in/out) are explicit.
- [x] Acceptance criteria are testable.
- [x] Dependencies and known risks are listed.

# Companion docs
- Product brief(s): `prod_004_claimlens_single_video_local_first_mvp`
- Architecture decision(s): `adr_001_single_video_local_first_pipeline`

# References
- ROADMAP.md
- README.md
- src/claimlens/cli.py
- src/claimlens/db.py
- src/claimlens/youtube.py
- logics/architecture/adr_001_single_video_local_first_pipeline.md

# AI Context
- Summary: MVP: Single Video Local First Pipeline
- Keywords: request-chain-scaffold, mvp: single video local first pipeline, development-ready
- Use when: You need to implement or review the scaffolded workflow for MVP: Single Video Local First Pipeline.
- Skip when: The change is unrelated to this scaffolded request chain.

# Backlog
- `item_014_implement_single_video_run_model_and_url_input`
- `item_015_make_subtitle_extraction_mandatory_and_add_transcript_cleanup`
- `item_016_add_openai_llm_analysis_for_cleaned_transcripts`
- `item_017_generate_direct_markdown_brief_from_llm_analysis`
- `item_018_design_optional_advanced_source_verification_mode`
- `item_019_build_local_html_process_page`
- `item_020_add_end_to_end_local_mvp_validation`
