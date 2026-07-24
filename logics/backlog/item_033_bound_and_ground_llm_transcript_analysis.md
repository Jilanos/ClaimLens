## item_033_bound_and_ground_llm_transcript_analysis - Bound and ground LLM transcript analysis
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Medium
> Theme: LLM reliability
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- Transcript length sent to OpenAI is unbounded.
- The analysis call does not explicitly request deterministic settings and extracted claims are not required to cite transcript evidence.
- Malformed OpenAI responses and network failures can surface as raw exceptions.

# Scope
- In:
  - Add transcript token/character bounds or chunking before analysis.
  - Set deterministic model parameters such as temperature=0 where supported by the API.
  - Require each notable claim to include an excerpt from the transcript or mark it ungrounded.
  - Handle OpenAI HTTP, URL, timeout, malformed JSON, empty choices, and schema mismatch errors with ClaimLens-level errors.
  - Avoid duplicate concurrent paid analysis calls for the same run/action.
- Out:
  - Changing the selected OpenAI model unless needed for compatibility.
  - Adding a second LLM provider.

# Acceptance criteria
- AC1: Long transcripts are bounded or chunked before LLM submission.
- AC2: Notable claims are grounded with transcript excerpts in persisted analysis data.
- AC3: OpenAI/network malformed responses produce controlled errors and logs.
- AC4: Tests cover long transcript handling, claim grounding, and failure mapping.

# AC Traceability
- request-AC5 -> This backlog slice. Proof: AC1: Long transcripts are bounded or chunked before LLM submission.
- request-AC13 -> This backlog slice. Proof: AC2: Notable claims are grounded with transcript excerpts in persisted analysis data.
- request-AC16 -> This backlog slice. Proof: AC3: OpenAI/network malformed responses produce controlled errors and logs.
- request-AC18 -> This backlog slice. Proof: AC4: Tests cover long transcript handling, claim grounding, and failure mapping.
- request-AC6 -> This backlog slice. Evidence needed: YouTube channel-page scraping helpers that are outside the single-video MVP are isolated, disabled, or removed from exposed flows before online use.
- request-AC7 -> This backlog slice. Evidence needed: Source verification no longer relies on simple keyword polarity heuristics for supports/contradicts decisions and uses a review-aid vocabulary when evidence quality is insufficient.
- request-AC8 -> This backlog slice. Evidence needed: PubMed verification retrieves and stores real abstract/snippet evidence when available instead of treating titles as abstracts, and tests cover no-abstract fallback behavior.
- request-AC9 -> This backlog slice. Evidence needed: Verification confidence values are either removed or computed from documented evidence rules, and adapter/search errors are logged and surfaced distinctly from no-source results.
- request-AC10 -> This backlog slice. Evidence needed: Long-running analyze/verify/report actions run through an asynchronous job model with persisted status, retry-safe/idempotent behavior, polling or equivalent UI updates, and user-visible progress states.
- request-AC11 -> This backlog slice. Evidence needed: The process page has accessible labels, responsive layout improvements, controlled user-facing error messages, source video links, cleaned-transcript preview, and paginated or bounded run selection.
- request-AC12 -> This backlog slice. Evidence needed: SQLite connections use WAL and busy_timeout for concurrent web access, while migration behavior is formalized with versioned, tested migration steps before the next schema change.
- request-AC14 -> This backlog slice. Evidence needed: Runtime configuration does not depend on Path.cwd() in production paths and documents explicit environment/config-file precedence for deployed execution.
- request-AC15 -> This backlog slice. Evidence needed: Rate limiting or quota enforcement exists for costly/outbound actions at the application boundary, with documentation of any remaining reverse-proxy dependency.
- request-AC17 -> This backlog slice. Evidence needed: Structured application/access logging is available for online diagnostics without persisting secrets, and Python version expectations are aligned across local docs and CI.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_006_claimlens_online_readiness_audit_implementation`
- Architecture decision(s): (none yet)
- Request: `req_005_online_readiness_audit_implementation`
- Primary task(s): `task_006_orchestrate_online_readiness_audit_implementation`

# AI Context
- Summary: Bound and ground LLM transcript analysis
- Keywords: scaffolded-backlog, bound and ground llm transcript analysis, implementation-ready
- Use when: Implementing the scaffolded slice for Bound and ground LLM transcript analysis.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.

# Tasks
- `task_006_orchestrate_online_readiness_audit_implementation`

# Notes
- Task `task_006_orchestrate_online_readiness_audit_implementation` was finished via `logics-manager flow finish task` on 2026-07-24.
