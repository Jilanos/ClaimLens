## item_026_assess_evidence_into_non_binary_verdicts - Assess evidence into non-binary verdicts
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: High
> Theme: Verdict assessment
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- Retrieved sources need to be interpreted against the original claim without overstating certainty.
- Health/science evidence can be mixed, indirect, or insufficient.

# Scope
- In:
  - Add a mockable assessment boundary that compares claim text with candidate evidence.
  - Return verdict, supporting snippets, contradicting snippets, rationale, and human-review disclaimer.
  - Use conservative verdict rules for mixed or insufficient evidence.
  - Add tests for supported, contradicted, mixed, unclear, and no-source cases.
- Out:
  - Authoritative medical advice.
  - Automated clinical recommendations.
  - Single binary true/false verdicts.

# Acceptance criteria
- AC1: Assessment can classify mocked evidence into each supported verdict value.
- AC2: Supporting and contradicting cited phrases are retained in persisted evidence.
- AC3: Rationale explicitly mentions uncertainty when evidence is indirect or insufficient.
- AC4: Generated outputs include a human-review disclaimer.

# AC Traceability
- request-AC4 -> This backlog slice. Proof: AC1: Assessment can classify mocked evidence into each supported verdict value.
- request-AC5 -> This backlog slice. Proof: AC2: Supporting and contradicting cited phrases are retained in persisted evidence.
- request-AC6 -> This backlog slice. Proof: AC3: Rationale explicitly mentions uncertainty when evidence is indirect or insufficient.
- request-AC10 -> This backlog slice. Proof: AC4: Generated outputs include a human-review disclaimer.
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
- Summary: Assess evidence into non-binary verdicts
- Keywords: scaffolded-backlog, assess evidence into non-binary verdicts, implementation-ready
- Use when: Implementing the scaffolded slice for Assess evidence into non-binary verdicts.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.

# Tasks
- `task_005_orchestrate_advanced_source_verification_mode`

# Notes
- Task `task_005_orchestrate_advanced_source_verification_mode` was finished via `logics-manager flow finish task` on 2026-07-23.
