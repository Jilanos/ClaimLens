## req_002_audit_remediation_and_hardening - Audit Remediation and Hardening
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Complexity: Medium
> Theme: Quality
> Reminder: Update status/understanding/confidence and linked backlog/task references when you edit this doc.

# Needs
- Respond to the 2026-07-23 audit by turning the non-blocking findings into tracked implementation work.
- Remove the most immediate reliability risk by ensuring SQLite connections are closed deterministically.
- Make configuration behavior explicit and robust enough for installed CLI usage and malformed local files.
- Add a minimal automated quality gate so future changes run lint and tests consistently.
- Capture the schema migration policy before any production schema change requires versioned migrations.

# Context
- AUDIT.md gives the repository a commit-and-push green light, with minor and future hardening findings to plan through Logics.
- Milestone 1 is complete and Milestone 2 metadata ingestion is already scaffolded as a separate active chain.
- This chain should harden the local skeleton without expanding the product scope into ingestion, transcript creation, or analysis.
- The audit recommends priority order: close SQLite connections, add minimal CI, then define migrations before schema changes.

# Acceptance criteria
- AC1: SQLite helper paths close every opened connection deterministically while preserving current transaction behavior.
- AC2: Configuration default path behavior is either made install-safe or documented as repository-root execution behavior with tests covering the selected contract.
- AC3: Environment override behavior for output-related paths is made consistent or explicitly documented as intentionally limited for the MVP.
- AC4: Malformed numeric configuration values fail with a clear ClaimLens-level error message instead of an opaque conversion exception.
- AC5: A minimal CI workflow runs the established `ruff check .` and `pytest` validation commands on push and pull request events.
- AC6: Schema versioning expectations are documented before any schema version 2 change, including when migrations are required and how they should be validated.
- AC7: README, ROADMAP, or another appropriate project doc reflects any operator-facing changes introduced by the audit response.
- AC8: The audit response closes only after `ruff check .`, `pytest`, and `logics-manager lint --require-status` pass locally.

# AC Traceability
- AC1 -> `task_003_orchestrate_audit_remediation_and_hardening`. Proof: `src/claimlens/db.py` uses `contextlib.closing` around helper-owned connections; `tests/test_db.py` asserts `init_db` and `table_names` close connections.
- AC2 -> `task_003_orchestrate_audit_remediation_and_hardening`. Proof: `README.md` documents the repository-root default config contract; `tests/test_config.py` covers default loading without a file.
- AC3 -> `task_003_orchestrate_audit_remediation_and_hardening`. Proof: `src/claimlens/config.py` supports `CLAIMLENS_DB`, `CLAIMLENS_OUTPUTS`, `CLAIMLENS_TRANSCRIPTS`, and `CLAIMLENS_BRIEFS`; `tests/test_config.py` covers the overrides.
- AC4 -> `task_003_orchestrate_audit_remediation_and_hardening`. Proof: `ConfigError` wraps invalid pipeline integer settings; `tests/test_config.py` covers the error message.
- AC5 -> `task_003_orchestrate_audit_remediation_and_hardening`. Proof: `.github/workflows/ci.yml` runs `ruff check .` and `pytest` on push and pull request events.
- AC6 -> `task_003_orchestrate_audit_remediation_and_hardening`. Proof: `README.md` documents schema version 1 as initialization-only and requires a tested migration path before schema version 2.
- AC7 -> `task_003_orchestrate_audit_remediation_and_hardening`. Proof: `README.md` and `ROADMAP.md` document operator-facing config, schema, CI, and migration-policy changes.
- AC8 -> `task_003_orchestrate_audit_remediation_and_hardening`. Proof: `.venv/bin/ruff check .`, `.venv/bin/pytest`, `logics-manager lint --require-status`, and `logics-manager audit --legacy-cutoff-version 1.1.0 --group-by-doc` passed locally.

# Definition of Ready (DoR)
- [x] Problem statement is explicit and user impact is clear.
- [x] Scope boundaries (in/out) are explicit.
- [x] Acceptance criteria are testable.
- [x] Dependencies and known risks are listed.

# Companion docs
- Product brief(s): `prod_003_claimlens_audit_remediation_and_hardening`
- Architecture decision(s): (none yet)

# References
- AUDIT.md
- README.md
- ROADMAP.md
- pyproject.toml
- src/claimlens/config.py
- src/claimlens/db.py
- tests/test_config.py
- tests/test_db.py

# AI Context
- Summary: Audit Remediation and Hardening
- Keywords: request-chain-scaffold, audit remediation and hardening, development-ready
- Use when: You need to implement or review the scaffolded workflow for Audit Remediation and Hardening.
- Skip when: The change is unrelated to this scaffolded request chain.

# Backlog
- `item_010_close_sqlite_connections_deterministically`
- `item_011_harden_configuration_loading_contract`
- `item_012_add_minimal_ci_quality_gate`
- `item_013_document_schema_migration_policy`
