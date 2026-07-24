## req_009_make_process_state_live_and_verification_outcomes_actionable - Make process state live and verification outcomes actionable
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Complexity: High
> Theme: Process UX and verification reliability
> Reminder: Update status/understanding/confidence and linked backlog/task references when you edit this doc.

# Needs
- Replace the static process-page snapshot with a lightweight live job view: it must show meaningful queued, running, succeeded, failed, and warning states without a fake percentage progress value.
- Hide per-run OpenAI, Semantic Scholar, and NCBI key inputs for authenticated users when the corresponding encrypted profile key is already available; retain the inputs for guests and for providers without a saved key.
- Normalize caption-segment line breaks into readable paragraphs for cleaned transcripts while retaining the raw timestamped segments in SQLite.
- Make source-verification outcomes actionable: distinguish no candidates from adapter failure and rate limiting, and do not label an all-adapter-failed run as source-verified.

# Context
- Jobs are submitted to a background executor and are set to running at 5%, then directly to 100%; the Process page is server-rendered once and has no polling or auto-refresh.
- API key resolution already prefers authenticated users' encrypted saved keys, but the Process controls render manual key fields unconditionally.
- clean_transcript_text currently joins each source subtitle segment with a newline, preserving the provider's short caption chunks in the cleaned artifact and LLM input.
- For video F6OKdue0UBw, source verification produced no evidence because Semantic Scholar returned HTTP 429 and PubMed returned no candidates; the markdown report still announced advanced source verification as completed.
- The verified report currently renders only supporting and contradicting snippets, so context-only candidates and adapter errors are not visible as first-class outcome states.

# Acceptance criteria
- The Process page no longer renders a numeric job progress percentage; it renders an explicit status and message for each job.
- While a visible run has queued or running jobs, the browser refreshes its job and step state through an authenticated, run-scoped JSON endpoint at a bounded interval no shorter than two seconds, and stops polling after terminal state.
- The live refresh updates job status, step status, failure message, next available action, and output links without requiring the user to open a new page; requests that return unchanged state avoid a full DOM rewrite.
- For an authenticated user with a saved OpenAI, Semantic Scholar, or NCBI key, the corresponding Process-page manual key field is absent and the action uses the saved key. Guests and authenticated users without that provider key still see the manual field.
- The API never exposes plaintext saved keys in HTML, JSON status responses, logs, or tests.
- Cleaned transcript text joins consecutive caption segments into readable paragraphs rather than retaining arbitrary provider line breaks; sentence boundaries and a bounded paragraph length determine paragraph breaks.
- Raw transcript text and timestamped segments remain persisted unchanged, and cleaned-text reflow does not remove or duplicate words across segment boundaries.
- Source verification records and presents per-adapter outcomes for each run, including no candidates, HTTP 429/rate limit, timeout, and other adapter errors.
- A verification run for which every configured adapter failed is surfaced as failed or completed with warnings and is not presented as a successfully source-verified brief. Mixed outcomes remain explicit about which adapters supplied usable candidates.
- Semantic Scholar HTTP 429 handling is bounded: it respects Retry-After when supplied, uses a finite retry policy, and gives the user a clear remediation message that a saved Semantic Scholar key can improve quota.
- Focused tests cover live status polling authorization and terminal behavior, conditional key fields, transcript paragraph reflow, and verification outcomes for rate limits, no candidates, and partial adapter success. Ruff, pytest, Logics lint, and Logics audit pass before closeout.

# Definition of Ready (DoR)
- [x] Problem statement is explicit and user impact is clear.
- [x] Scope boundaries (in/out) are explicit.
- [x] Acceptance criteria are testable.
- [x] Dependencies and known risks are listed.

# Companion docs
- Product brief(s): `prod_013_live_claimlens_process_feedback_and_trustworthy_verification_results`
- Architecture decision(s): (none yet)

# References
- src/claimlens/web.py
- src/claimlens/pipeline.py
- src/claimlens/verification.py
- src/claimlens/briefs.py
- src/claimlens/api_keys.py
- tests/test_analysis_briefs_web.py
- tests/test_pipeline.py
- tests/test_verification.py
- docs/deployment-paulmondou-infra.md

# AI Context
- Summary: Make process state live and verification outcomes actionable
- Keywords: request-chain-scaffold, make process state live and verification outcomes actionable, development-ready
- Use when: You need to implement or review the scaffolded workflow for Make process state live and verification outcomes actionable.
- Skip when: The change is unrelated to this scaffolded request chain.

# Backlog
- `item_057_add_bounded_live_process_job_state_refresh`
- `item_058_hide_redundant_process_api_key_fields_for_saved_profiles`
- `item_059_reflow_cleaned_transcript_segments_into_readable_paragraphs`
- `item_060_report_source_verification_limits_and_rate_limited_adapters_honestly`
- `item_061_validate_live_process_feedback_and_verification_outcome_delivery`
