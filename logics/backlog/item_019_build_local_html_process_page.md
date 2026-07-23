## item_019_build_local_html_process_page - Build local HTML process page
> From version: 1.0.0
> Schema version: 1.0
> Status: Ready
> Understanding: 90%
> Confidence: 85%
> Progress: 0%
> Complexity: High
> Theme: Local-first UI
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- The user needs to see each pipeline step, understand failures, and trigger the next eligible action.
- The UI should be local-first now and deployable on a VPS later.

# Scope
- In:
  - Serve a local HTML page that lists run status, step status, failure causes, and output links.
  - Provide controls for launching the next eligible step.
  - Support entry of one video URL and OpenAI key at the start without persisting the secret.
  - Use configurable host/port and avoid hardcoded local-only assumptions.
  - Add tests for process-state rendering.
- Out:
  - Multi-user auth.
  - Hosted SaaS deployment.
  - Background scheduler.

# Acceptance criteria
- AC1: A local process page can create or load a single video run.
- AC2: Each step shows pending/running/succeeded/failed/skipped status.
- AC3: Failed steps show a clear cause and prevent ineligible downstream execution.
- AC4: The next eligible step can be launched from the page.
- AC5: Host/port and output paths are configurable for later VPS deployment.

# AC Traceability
- request-AC8 -> This backlog slice. Proof: AC1: A local process page can create or load a single video run.
- request-AC9 -> This backlog slice. Proof: AC2: Each step shows pending/running/succeeded/failed/skipped status.
- request-AC10 -> This backlog slice. Proof: AC3: Failed steps show a clear cause and prevent ineligible downstream execution.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_004_claimlens_single_video_local_first_mvp`
- Architecture decision(s): (none yet)
- Request: `req_003_mvp_single_video_local_first_pipeline`
- Primary task(s): `task_004_orchestrate_single_video_local_first_mvp`

# AI Context
- Summary: Build local HTML process page
- Keywords: scaffolded-backlog, build local html process page, implementation-ready
- Use when: Implementing the scaffolded slice for Build local HTML process page.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.
