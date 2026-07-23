## item_022_define_source_adapter_interfaces - Define source adapter interfaces
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Medium
> Theme: Source adapters
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- Verification needs external source retrieval while remaining mockable and deterministic in tests.
- PubMed and Semantic Scholar have different APIs and metadata shapes.

# Scope
- In:
  - Define SourceAdapter and SourceCandidate contracts.
  - Define query inputs derived from notable claims and health/science context.
  - Normalize source metadata fields across adapters.
  - Add tests for adapter contracts and query construction.
- Out:
  - Live API calls in unit tests.
  - Broad web search adapter.
  - Ranking model beyond deterministic metadata and configured limits.

# Acceptance criteria
- AC1: PubMed and Semantic Scholar adapters conform to one shared interface.
- AC2: Source candidates include title, URL, source, publication date, abstract/snippet, and adapter name.
- AC3: Query construction is deterministic and covered by tests.
- AC4: Adapter failures are captured without failing unrelated completed pipeline steps.

# AC Traceability
- request-AC2 -> This backlog slice. Proof: AC1: PubMed and Semantic Scholar adapters conform to one shared interface.
- request-AC3 -> This backlog slice. Proof: AC2: Source candidates include title, URL, source, publication date, abstract/snippet, and adapter name.
- request-AC10 -> This backlog slice. Proof: AC3: Query construction is deterministic and covered by tests.
- request-AC4 -> This backlog slice. Evidence needed: Each checked claim receives one non-binary verdict: supported, contradicted, mixed, unclear, or not_checked.
- request-AC5 -> This backlog slice. Evidence needed: Each verdict stores cited evidence snippets separated into supporting and contradicting evidence where available.
- request-AC6 -> This backlog slice. Evidence needed: Evidence assessment includes a concise rationale and a human-review disclaimer for health/science outputs.
- request-AC7 -> This backlog slice. Evidence needed: The Markdown brief renderer can produce a source-verified variant with citations, evidence snippets, verdicts, and a visible source-verification status.
- request-AC8 -> This backlog slice. Evidence needed: The local HTML process page shows the verification step status, failure causes, verdict summaries, source counts, and links to verified outputs.
- request-AC9 -> This backlog slice. Evidence needed: The implementation remains local-first and VPS-ready: API keys are runtime/config inputs only, host/path settings remain configurable, and generated outputs do not persist secrets.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_005_claimlens_advanced_source_verification_mode`
- Architecture decision(s): (none yet)
- Request: `req_004_advanced_source_verification_mode`
- Primary task(s): `task_005_orchestrate_advanced_source_verification_mode`

# AI Context
- Summary: Define source adapter interfaces
- Keywords: scaffolded-backlog, define source adapter interfaces, implementation-ready
- Use when: Implementing the scaffolded slice for Define source adapter interfaces.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.

# Tasks
- `task_005_orchestrate_advanced_source_verification_mode`

# Notes
- Task `task_005_orchestrate_advanced_source_verification_mode` was finished via `logics-manager flow finish task` on 2026-07-23.
