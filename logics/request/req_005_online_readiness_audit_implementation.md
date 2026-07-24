## req_005_online_readiness_audit_implementation - Online Readiness Audit Implementation
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Complexity: High
> Theme: Online readiness
> Reminder: Update status/understanding/confidence and linked backlog/task references when you edit this doc.

# Needs
- Turn the selected 2026-07-24 pre-deployment audit findings into implementation-ready Logics work.
- Prepare the local-first MVP for controlled online exposure without implementing the OpenAI key model or reverse-proxy hosting decision yet.
- Add web safety controls, report viewing and download, async UX, robust analysis boundaries, stronger source verification, and production runtime hardening.
- Make the final report rendering language configurable; transcript language selection can be explored later and must not block report-language configuration.

# Context
- The operator accepted B3 through B6, F2 through F5, S1 through S5, U1 through U6, and T1 through T8 from audit_before_online_deployement.md.
- B1 OpenAI key model and B2 reverse-proxy HTTPS/login are explicitly standby and must be documented but not implemented in this chain.
- F6 was rejected: do not add new work solely to make the human-review disclaimer more prominent beyond preserving existing disclaimers where already required.
- F1 is partially accepted only as configurable final report language; configurable subtitle language remains a later product decision unless needed to support report language.
- The current web server is a simple local HTTP process page; this chain should harden it enough for guarded use behind future deployment controls without turning it into a full multi-user SaaS.
- The implementation must stay deterministic and testable without live OpenAI, YouTube, PubMed, or Semantic Scholar calls in CI.

# Acceptance criteria
- AC1: Web POST handlers validate Content-Length, enforce a small configurable maximum request size, reject malformed bodies with controlled responses, and require CSRF protection for mutating actions.
- AC2: The web UI can display the generated Markdown brief as safe HTML and download it as Markdown through routes that resolve reports by validated run/video identifiers and prevent path traversal.
- AC3: Final report rendering language is configurable from CLI/config/web flow, persisted or passed through the run as appropriate, and covered by tests without requiring configurable subtitle language.
- AC4: Single-video reports include real available video metadata such as title, source URL, author/channel, date, and duration when retrievable, while preserving graceful fallback behavior.
- AC5: The analysis step bounds or chunks long transcripts, uses deterministic OpenAI settings where supported, and grounds each extracted notable claim with a transcript excerpt.
- AC6: YouTube channel-page scraping helpers that are outside the single-video MVP are isolated, disabled, or removed from exposed flows before online use.
- AC7: Source verification no longer relies on simple keyword polarity heuristics for supports/contradicts decisions and uses a review-aid vocabulary when evidence quality is insufficient.
- AC8: PubMed verification retrieves and stores real abstract/snippet evidence when available instead of treating titles as abstracts, and tests cover no-abstract fallback behavior.
- AC9: Verification confidence values are either removed or computed from documented evidence rules, and adapter/search errors are logged and surfaced distinctly from no-source results.
- AC10: Long-running analyze/verify/report actions run through an asynchronous job model with persisted status, retry-safe/idempotent behavior, polling or equivalent UI updates, and user-visible progress states.
- AC11: The process page has accessible labels, responsive layout improvements, controlled user-facing error messages, source video links, cleaned-transcript preview, and paginated or bounded run selection.
- AC12: SQLite connections use WAL and busy_timeout for concurrent web access, while migration behavior is formalized with versioned, tested migration steps before the next schema change.
- AC13: Network and OpenAI failures including URLError, timeouts, malformed API responses, and adapter failures return controlled errors and structured logs without leaking internals to the UI.
- AC14: Runtime configuration does not depend on Path.cwd() in production paths and documents explicit environment/config-file precedence for deployed execution.
- AC15: Rate limiting or quota enforcement exists for costly/outbound actions at the application boundary, with documentation of any remaining reverse-proxy dependency.
- AC16: Re-analysis avoids unbounded duplicate summaries/claims and prevents duplicate concurrent paid calls for the same run/action.
- AC17: Structured application/access logging is available for online diagnostics without persisting secrets, and Python version expectations are aligned across local docs and CI.
- AC18: Validation passes with ruff, pytest, compileall where applicable, logics-manager lint --require-status, and logics-manager audit before closeout.

# Definition of Ready (DoR)
- [x] Problem statement is explicit and user impact is clear.
- [x] Scope boundaries (in/out) are explicit.
- [x] Acceptance criteria are testable.
- [x] Dependencies and known risks are listed.

# Companion docs
- Product brief(s): `prod_006_claimlens_online_readiness_audit_implementation`
- Architecture decision(s): (none yet)

# References
- audit_before_online_deployement.md
- src/claimlens/web.py
- src/claimlens/analysis.py
- src/claimlens/verification.py
- src/claimlens/youtube.py
- src/claimlens/db.py
- src/claimlens/config.py
- src/claimlens/briefs.py
- README.md
- ROADMAP.md

# AI Context
- Summary: Online Readiness Audit Implementation
- Keywords: request-chain-scaffold, online readiness audit implementation, development-ready
- Use when: You need to implement or review the scaffolded workflow for Online Readiness Audit Implementation.
- Skip when: The change is unrelated to this scaffolded request chain.

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
