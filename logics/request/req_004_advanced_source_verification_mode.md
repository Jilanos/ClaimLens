## req_004_advanced_source_verification_mode - Advanced Source Verification Mode
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Complexity: High
> Theme: Advanced source verification
> Reminder: Update status/understanding/confidence and linked backlog/task references when you edit this doc.

# Needs
- Add an optional source verification mode after the existing OpenAI transcript analysis step.
- Use PubMed and Semantic Scholar as the first supported source adapters for health and science claims.
- Assess only notable claims extracted from the cleaned transcript analysis, not arbitrary new claims.
- Produce non-binary verdicts for each checked claim: supported, contradicted, mixed, unclear, or not_checked.
- Attach cited evidence snippets that indicate whether each source supports or contradicts the claim.
- Expose the verification step through both the CLI and the local HTML process page.
- Render verified Markdown briefs with citations, evidence snippets, and a clear human-review disclaimer.

# Context
- The current MVP generates Markdown briefs directly from OpenAI transcript analysis and labels them not advanced-source-verified.
- The existing SQLite schema already has sources and claim_sources tables, but no concrete adapter, evidence, or verdict workflow.
- The existing source configuration has advanced_source_verification disabled by default.
- The target domain for this mode is health and science; PubMed and Semantic Scholar are a better initial fit than broad web search.
- Verification must remain local-first and testable without live API calls by mocking adapter and LLM boundaries.
- Verdicts must be review aids, not automated final medical, legal, financial, or scientific authority judgments.

# Acceptance criteria
- AC1: A user can enable source verification for an existing single-video run from the CLI or local HTML process page without changing the base MVP default.
- AC2: The verification step reads stored notable claims and queries PubMed and Semantic Scholar through mockable adapter interfaces.
- AC3: Candidate sources are persisted with enough metadata to audit title, URL, publisher/source, publication date, snippet, retrieval time, adapter, and matched claim.
- AC4: Each checked claim receives one non-binary verdict: supported, contradicted, mixed, unclear, or not_checked.
- AC5: Each verdict stores cited evidence snippets separated into supporting and contradicting evidence where available.
- AC6: Evidence assessment includes a concise rationale and a human-review disclaimer for health/science outputs.
- AC7: The Markdown brief renderer can produce a source-verified variant with citations, evidence snippets, verdicts, and a visible source-verification status.
- AC8: The local HTML process page shows the verification step status, failure causes, verdict summaries, source counts, and links to verified outputs.
- AC9: The implementation remains local-first and VPS-ready: API keys are runtime/config inputs only, host/path settings remain configurable, and generated outputs do not persist secrets.
- AC10: Tests cover adapter query construction, mocked PubMed/Semantic Scholar responses, source persistence, verdict assessment, verified brief rendering, and HTML process-state rendering without live network calls.

# Definition of Ready (DoR)
- [x] Problem statement is explicit and user impact is clear.
- [x] Scope boundaries (in/out) are explicit.
- [x] Acceptance criteria are testable.
- [x] Dependencies and known risks are listed.

# Companion docs
- Product brief(s): `prod_005_claimlens_advanced_source_verification_mode`
- Architecture decision(s): (none yet)

# References
- README.md
- config/claimlens.example.toml
- src/claimlens/analysis.py
- src/claimlens/briefs.py
- src/claimlens/cli.py
- src/claimlens/db.py
- src/claimlens/pipeline.py
- src/claimlens/web.py
- logics/architecture/adr_001_single_video_local_first_pipeline.md
- logics/request/req_003_mvp_single_video_local_first_pipeline.md
- logics/product/prod_004_claimlens_single_video_local_first_mvp.md

# AI Context
- Summary: Advanced Source Verification Mode
- Keywords: request-chain-scaffold, advanced source verification mode, development-ready
- Use when: You need to implement or review the scaffolded workflow for Advanced Source Verification Mode.
- Skip when: The change is unrelated to this scaffolded request chain.

# Backlog
- `item_021_add_optional_verification_mode_controls`
- `item_022_define_source_adapter_interfaces`
- `item_023_implement_pubmed_source_adapter`
- `item_024_implement_semantic_scholar_source_adapter`
- `item_025_persist_verification_evidence_and_verdict_state`
- `item_026_assess_evidence_into_non_binary_verdicts`
- `item_027_render_source_verified_markdown_briefs`
- `item_028_expose_verification_state_in_local_html_page`
- `item_029_add_source_verification_validation_and_documentation`
