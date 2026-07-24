## req_010_harden_claimlens_production_reliability_and_verification_integrity - Harden ClaimLens production reliability and verification integrity
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Complexity: High
> Theme: Production reliability and evidence integrity
> Reminder: Update status/understanding/confidence and linked backlog/task references when you edit this doc.

# Needs
- Make persisted web jobs recoverable after a process or container restart so a queued or running action cannot remain permanently blocked.
- Make action rate limiting correct behind the documented Caddy reverse proxy and fair across users.
- Apply the configured source-verification switches consistently in the CLI and web workflows.
- Handle provider quotas without retry storms and ensure verification artifacts describe their actual evidentiary status.
- Improve claim retrieval relevance and long-transcript coverage so reports do not silently overstate their scope.
- Cover the browser-facing live workflow and operational recovery paths with deterministic integration tests.

# Context
- Jobs are inserted into SQLite and then submitted to an in-process ThreadPoolExecutor. A restart loses the executor queue while queued or running rows still reject the same action.
- The deployment uses Caddy as a reverse proxy, while the current in-memory rate limiter keys actions by the direct socket peer IP.
- Source configuration flags are loaded but the web flow unconditionally constructs PubMed and Semantic Scholar adapters.
- Semantic Scholar HTTP 429 is retried after a delay capped at three seconds for every claim, which can repeatedly call a provider still in cooldown.
- A completed-with-warnings verification writes a file named .verified.md and retains a source-verified report heading even when no usable evidence exists.
- Verification searches use the first twelve filtered claim words and analysis truncates long transcripts to their head and tail without exposing coverage in the final report.
- Existing tests cover state helper functions but do not exercise the HTTP polling flow, container restart recovery, or reverse-proxy client identity behavior.

# Acceptance criteria
- On application startup, every stale queued or running job is deterministically recovered, resumed, or moved to a retryable terminal state with an actionable message; no stale row can prevent the user from submitting the action again.
- Job execution has a recorded lease or heartbeat and bounded timeout policy, and the Process page represents orphaned work as failed or retryable rather than indefinitely running.
- In the documented Caddy deployment, rate limits use a trusted client identity or an authenticated account/session identity; a shared proxy IP cannot exhaust every user's action budget, and forwarded headers are never trusted from arbitrary direct clients.
- Rate-limit state is suitable for the deployed process model and persists or is explicitly centralized when multiple instances are enabled.
- The advanced source-verification, PubMed, Semantic Scholar, and web-search configuration switches control the adapters and controls actually exposed by both CLI and web workflows.
- A provider HTTP 429 creates a shared cooldown that honors Retry-After when present, avoids premature retries, and gives a retry/remediation state without repeatedly consuming worker capacity for each claim.
- A report is described as source verified only when usable evidence was retrieved; all-warning or no-evidence attempts are exported and displayed with distinct names, status, and adapter diagnostics.
- Claim search queries are generated or normalized for retrieval relevance, adapter selection is domain-aware, and each verification run has a configured claim and time budget.
- Long transcript analysis preserves coverage across the full transcript through chunking and consolidation, or visibly records the exact omitted coverage in the resulting report.
- Deterministic tests cover restart recovery, rate-limit client identity, source configuration switches, provider cooldown behavior, report status semantics, long-transcript coverage, and authenticated HTTP polling. Ruff, pytest, Logics lint, and Logics audit pass before closeout.

# Definition of Ready (DoR)
- [x] Problem statement is explicit and user impact is clear.
- [x] Scope boundaries (in/out) are explicit.
- [x] Acceptance criteria are testable.
- [x] Dependencies and known risks are listed.

# Companion docs
- Product brief(s): `prod_014_reliable_claimlens_jobs_and_evidence_aware_reports`
- Architecture decision(s): (none yet)

# References
- src/claimlens/web.py
- src/claimlens/db.py
- src/claimlens/config.py
- src/claimlens/verification.py
- src/claimlens/analysis.py
- src/claimlens/briefs.py
- src/claimlens/pipeline.py
- tests/test_analysis_briefs_web.py
- tests/test_db.py
- tests/test_verification.py
- docs/deployment-paulmondou-infra.md

# AI Context
- Summary: Harden ClaimLens production reliability and verification integrity
- Keywords: request-chain-scaffold, harden claimlens production reliability and verification integrity, development-ready
- Use when: You need to implement or review the scaffolded workflow for Harden ClaimLens production reliability and verification integrity.
- Skip when: The change is unrelated to this scaffolded request chain.

# Backlog
- `item_062_recover_durable_jobs_after_process_restart`
- `item_063_make_web_action_rate_limits_proxy_aware_and_durable`
- `item_064_apply_source_verification_configuration_switches`
- `item_065_control_source_provider_quotas_and_report_verification_truthfully`
- `item_066_improve_claim_retrieval_relevance_and_transcript_coverage`
- `item_067_add_production_workflow_integration_coverage`
