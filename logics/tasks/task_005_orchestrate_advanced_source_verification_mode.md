## task_005_orchestrate_advanced_source_verification_mode - Orchestrate Advanced Source Verification Mode
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
- [x] 1. Confirm the optional verification mode remains disabled by default and add explicit activation controls.
- [x] 2. Define adapter and evidence contracts before implementing concrete PubMed and Semantic Scholar retrieval.
- [x] 3. Implement mocked, deterministic PubMed and Semantic Scholar boundaries.
- [x] 4. Extend persistence for verification runs, source candidates, evidence snippets, and verdict state.
- [x] 5. Implement conservative evidence assessment into non-binary verdicts with supporting and contradicting snippets.
- [x] 6. Render source-verified Markdown briefs without regressing unverified brief output.
- [x] 7. Expose verification status, controls, failures, source counts, and output links in the local HTML page.
- [x] 8. Document usage, key handling, and manual smoke tests.
- [x] 9. Validate with deterministic tests plus Logics lint and audit.
- [x] 10. ADR 009 checkpoint: update affected Logics docs during each meaningful wave and leave the repo commit-ready.
- [x] 11. Keep commit creation under operator control; do not force one commit per micro-step.
- [x] 12. GATE: do not close until lint, audit, and verification tests pass.
- [x] ADR 009 checkpoint: update affected Logics docs during each meaningful wave and leave the repo commit-ready.
- [x] Keep commit creation under operator control; do not force one commit per micro-step.
- [x] GATE: do not close until lint, audit, and scaffold validation pass.

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

# Definition of Done (DoD)
- [x] Generated request, product, backlog, and task docs are present.
- [x] Context-pack handoff is available when requested.
- [x] Validation passes.
- [x] Meaningful waves followed ADR 009: affected docs updated and the repo left commit-ready without automatic commits.

# AC Traceability
- request-AC1 -> This task. Proof: `claimlens verify-sources` and alias `source-check` enable optional verification for analyzed videos, while base runs remain unchanged and `advanced_source_verification` stays false by default.
- request-AC2 -> This task. Proof: `verification.SourceAdapter`, `PubMedAdapter`, and `SemanticScholarAdapter` read stored notable claims and expose mockable search boundaries covered by `tests/test_verification.py`.
- request-AC3 -> This task. Proof: schema v3 stores normalized sources with title, URL, publisher, publication date, snippet, retrieval metadata, adapter, external ID, and claim links.
- request-AC4 -> This task. Proof: `assess_claim_evidence` and `db.update_claim_verdict` persist supported, contradicted, mixed, unclear, and not_checked verdicts for checked claims.
- request-AC5 -> This task. Proof: `evidence_snippets` persists cited supporting and contradicting snippets separately with source and claim references.
- request-AC6 -> This task. Proof: verdict rationales include the health/science human-review disclaimer and conservative unclear/not_checked handling.
- request-AC7 -> This task. Proof: `generate_verified_brief` renders `<video_id>.verified.md` with source-verification status, verdicts, snippets, citations, and disclaimer.
- request-AC8 -> This task. Proof: the HTML process page exposes `source_verification` controls, status, failure path, source/evidence counts, and verified output links.
- request-AC9 -> This task. Proof: API keys are runtime/config inputs only, paths and host remain configurable, and generated SQLite/Markdown/HTML outputs do not persist secrets.
- request-AC10 -> This task. Proof: `.venv/bin/pytest` passed 33 tests covering adapter query construction, mocked retrieval, persistence, verdict assessment, verified brief rendering, and HTML state without live network calls.

# Validation
- `.venv/bin/ruff check .` passed.
- `.venv/bin/pytest` passed with 33 tests.
- `.venv/bin/python -m compileall -q src tests` passed.
- `logics-manager lint --require-status` passed.
- `logics-manager audit --group-by-doc` passed before closeout with only deferred-proof warnings.
- Implemented optional PubMed/Semantic Scholar source verification with CLI aliases verify-sources/source-check, HTML source_verification controls, schema v3 verification_runs/evidence_snippets, normalized source candidates, conservative non-binary verdicts, supporting/contradicting snippets, verified Markdown brief rendering, README smoke docs, and mocked deterministic tests. Validation passed: .venv/bin/ruff check ., .venv/bin/pytest (33 passed), .venv/bin/python -m compileall -q src tests, logics-manager lint --require-status, logics-manager audit --group-by-doc.
- Finish workflow executed on 2026-07-23.
- Linked backlog/request close verification passed.

# Report
- Implementation complete.
- Finished on 2026-07-23.
- Linked backlog item(s): `item_021_add_optional_verification_mode_controls`, `item_022_define_source_adapter_interfaces`, `item_023_implement_pubmed_source_adapter`, `item_024_implement_semantic_scholar_source_adapter`, `item_025_persist_verification_evidence_and_verdict_state`, `item_026_assess_evidence_into_non_binary_verdicts`, `item_027_render_source_verified_markdown_briefs`, `item_028_expose_verification_state_in_local_html_page`, `item_029_add_source_verification_validation_and_documentation`
- Related request(s): `req_004_advanced_source_verification_mode`

# AI Context
- Summary: Orchestrate Advanced Source Verification Mode
- Keywords: scaffolded-task, request-chain-scaffold, orchestration
- Use when: Coordinating implementation of a scaffolded request chain.
- Skip when: Working on one isolated sibling slice.

# Links
- Request: `req_004_advanced_source_verification_mode`
- Product brief(s): `prod_005_claimlens_advanced_source_verification_mode`
- Architecture decision(s): (none yet)
