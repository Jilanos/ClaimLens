## req_006_deployable_web_auth_and_api_key_management - Deployable Web Auth And API Key Management
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Complexity: High
> Theme: Deployable web application
> Reminder: Update status/understanding/confidence and linked backlog/task references when you edit this doc.

# Needs
- Prepare ClaimLens to run as a deployable web application behind the existing paulmondou-infra Docker Compose and Caddy VPS stack.
- Add first-party user login so authenticated users can save and reuse their API keys across runs.
- Store authenticated users' API keys in the database in the most secure practical way for a small self-hosted SQLite app: encrypted at rest with a deployment secret kept outside the database, never plaintext, never logged, and never rendered back in full.
- Keep guest mode available: non-logged users can still run processes, but must enter required API keys during each process and those guest keys must remain request/job-local only.
- Allow PubMed and Semantic Scholar verification to run without user-provided API keys, while still allowing logged users to save optional NCBI and Semantic Scholar keys for higher quotas or reliability.
- Add a top navigation bar with login/logout state, a login page, and an authenticated options page where users can add, update, mask, test, and delete supported API keys.

# Context
- The current ClaimLens web UI is a local process page with CSRF, local rate limiting, async jobs, report viewing, and Markdown download.
- The current deployment infra lives in /home/paul/dev/paulmondou-infra and uses Docker Compose plus Caddy. Existing public traffic terminates at Caddy and reverse proxies app containers by internal service name.
- paulmondou-infra currently has one dynamic app service named app for Kapsule, static sites, Caddy security headers, archive-mode deploy support, and environment-driven domains.
- ClaimLens must be added as a separate deployable application, not folded into Kapsule.
- B1/B2 from the previous audit remain product/deployment decisions, but this request moves them forward by adding user auth, HTTPS/reverse-proxy readiness, and key handling needed for safe deployment.
- YouTube transcript fetching from a VPS can be blocked by IP. A deployable ClaimLens must not depend solely on VPS-side youtube-transcript-api success; it needs a user-facing transcript fallback such as upload/paste.
- The implementation must remain testable without live OpenAI, PubMed, Semantic Scholar, YouTube, or VPS access in CI.

# Acceptance criteria
- AC1: ClaimLens has a deployable runtime shape with a Dockerfile or equivalent container entrypoint, production config/env variables, healthcheck, persistent data paths, and documentation compatible with paulmondou-infra.
- AC2: paulmondou-infra integration requirements are documented precisely, including a new ClaimLens service, CLAIMLENS_DOMAIN, CLAIMLENS_APP_DIR, internal port, Caddy reverse_proxy block, volumes, environment variables, deploy.sh DEPLOY_APP_REPOS usage, and backup expectations.
- AC3: Web authentication exists with login, logout, password hashing, secure session cookies, CSRF-compatible session handling, registration/bootstrap policy, and tests for successful and failed login flows.
- AC4: The top navigation bar shows application navigation and auth state, including login/logout and an authenticated Options link.
- AC5: Authenticated users can create, update, mask-display, test, and delete saved API keys for OpenAI, Semantic Scholar, and NCBI/PubMed from an Options page.
- AC6: Saved API keys are encrypted before database persistence using an authenticated encryption scheme and a deployment secret such as CLAIMLENS_KEY_ENCRYPTION_SECRET that is never stored in SQLite; plaintext keys are not logged, rendered, or written to reports/transcripts.
- AC7: Guest users can still create and run processes, but guest-entered keys are used only for the submitted job/action and are not persisted in users, runs, jobs, logs, reports, or transcripts.
- AC8: API key resolution order is explicit and tested: per-request guest key first, authenticated user's saved encrypted key second, server environment/config fallback only if enabled for that deployment, and no key where an adapter supports anonymous use.
- AC9: PubMed and Semantic Scholar verification can run anonymously without stored API keys, while authenticated saved keys are used when present to improve quota/reliability.
- AC10: User ownership and access control are enforced for runs, jobs, reports, transcripts, and options; guests cannot access authenticated users' resources and authenticated users cannot access each other's resources.
- AC11: The web UI supports transcript upload or paste fallback so a deployed VPS remains usable when YouTube blocks transcript fetching from the server IP.
- AC12: Database schema migrations add users, sessions, encrypted API keys, ownership fields, and transcript fallback records through versioned, tested migration steps from schema v4.
- AC13: Deployment docs include production security guidance: HTTPS only through Caddy, app bound internally, secure cookies, secret generation, backup/restore for SQLite plus encrypted-key secret, and operational warnings about losing CLAIMLENS_KEY_ENCRYPTION_SECRET.
- AC14: Tests cover auth, session security flags, API key encryption/decryption and redaction, guest key non-persistence, key resolution order, anonymous PubMed/Semantic behavior, access control, transcript upload fallback, and report access.
- AC15: Validation passes with ruff, pytest, compileall where applicable, logics-manager lint --require-status, and logics-manager audit before closeout.

# Definition of Ready (DoR)
- [x] Problem statement is explicit and user impact is clear.
- [x] Scope boundaries (in/out) are explicit.
- [x] Acceptance criteria are testable.
- [x] Dependencies and known risks are listed.

# Companion docs
- Product brief(s): `prod_007_claimlens_deployable_web_auth_and_api_key_management`
- Architecture decision(s): (none yet)

# References
- README.md
- ROADMAP.md
- config/claimlens.example.toml
- src/claimlens/web.py
- src/claimlens/config.py
- src/claimlens/db.py
- src/claimlens/analysis.py
- src/claimlens/verification.py
- src/claimlens/pipeline.py
- src/claimlens/youtube.py
- audit_before_online_deployement.md
- /home/paul/dev/paulmondou-infra/README.md
- /home/paul/dev/paulmondou-infra/docker-compose.yml
- /home/paul/dev/paulmondou-infra/Caddyfile
- /home/paul/dev/paulmondou-infra/.env.example
- /home/paul/dev/paulmondou-infra/deploy.sh

# AI Context
- Summary: Deployable Web Auth And API Key Management
- Keywords: request-chain-scaffold, deployable web auth and api key management, development-ready
- Use when: You need to implement or review the scaffolded workflow for Deployable Web Auth And API Key Management.
- Skip when: The change is unrelated to this scaffolded request chain.

# Backlog
- `item_041_package_claimlens_for_container_deployment`
- `item_042_specify_paulmondou_infra_integration`
- `item_043_implement_web_users_and_sessions`
- `item_044_encrypt_and_manage_user_api_keys`
- `item_045_add_guest_and_authenticated_process_key_resolution`
- `item_046_build_login_navigation_and_options_ui`
- `item_047_add_transcript_fallback_for_vps_blocked_youtube`
- `item_048_version_schema_and_validate_deployable_closeout`
