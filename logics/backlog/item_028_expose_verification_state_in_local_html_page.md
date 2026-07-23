## item_028_expose_verification_state_in_local_html_page - Expose verification state in local HTML page
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Medium
> Theme: Verification UI
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- The current HTML process page stops at base Markdown brief generation.
- Operators need to launch and inspect verification from the same local surface.

# Scope
- In:
  - Add verification step status to the process page.
  - Show source counts, verdict summaries, failure causes, and verified brief links.
  - Add form inputs for runtime PubMed/Semantic Scholar/OpenAI keys only when needed.
  - Add tests for process-state rendering and next-step eligibility.
- Out:
  - Multi-user hosted UI.
  - Authentication.
  - Background queue dashboard.

# Acceptance criteria
- AC1: HTML page can launch verification when analysis exists.
- AC2: HTML page prevents verification before analysis exists.
- AC3: HTML page displays verdict summary and source counts after verification.
- AC4: HTML tests run without network access.

# AC Traceability
- request-AC1 -> This backlog slice. Proof: AC1: HTML page can launch verification when analysis exists.
- request-AC8 -> This backlog slice. Proof: AC2: HTML page prevents verification before analysis exists.
- request-AC9 -> This backlog slice. Proof: AC3: HTML page displays verdict summary and source counts after verification.
- request-AC10 -> This backlog slice. Proof: AC4: HTML tests run without network access.
- request-AC5 -> This backlog slice. Evidence needed: Each verdict stores cited evidence snippets separated into supporting and contradicting evidence where available.
- request-AC6 -> This backlog slice. Evidence needed: Evidence assessment includes a concise rationale and a human-review disclaimer for health/science outputs.
- request-AC7 -> This backlog slice. Evidence needed: The Markdown brief renderer can produce a source-verified variant with citations, evidence snippets, verdicts, and a visible source-verification status.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_005_claimlens_advanced_source_verification_mode`
- Architecture decision(s): (none yet)
- Request: `req_004_advanced_source_verification_mode`
- Primary task(s): `task_005_orchestrate_advanced_source_verification_mode`

# AI Context
- Summary: Expose verification state in local HTML page
- Keywords: scaffolded-backlog, expose verification state in local html page, implementation-ready
- Use when: Implementing the scaffolded slice for Expose verification state in local HTML page.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.

# Tasks
- `task_005_orchestrate_advanced_source_verification_mode`

# Notes
- Task `task_005_orchestrate_advanced_source_verification_mode` was finished via `logics-manager flow finish task` on 2026-07-23.
