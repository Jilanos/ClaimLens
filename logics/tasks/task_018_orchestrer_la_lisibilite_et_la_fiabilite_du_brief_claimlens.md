## task_018_orchestrer_la_lisibilite_et_la_fiabilite_du_brief_claimlens - Orchestrer la lisibilité et la fiabilité du brief ClaimLens
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
- [x] 1. Cartographier les contrats de job, de polling, de rapport et de provider avant toute modification d'interface.
- [x] 2. Livrer puis vérifier la réconciliation d'état et la timeline permanente, afin que la nouvelle mise en page repose sur un état fiable.
- [x] 3. Implémenter la navigation supérieure et le brief HTML responsive à deux colonnes.
- [x] 4. Faire évoluer le contrat de vérification et le rendu vers la synthèse scientifique par claim.
- [x] 5. Ajouter la stratégie de cooldown/retry Semantic Scholar et vérifier que les erreurs récupérables ne remontent plus au brief.
- [x] 6. Exécuter les tests ciblés et complets, les contrôles d'accessibilité et les validations Logics avant closeout.
- [x] 7. ADR 009 checkpoint: mettre à jour les docs Logics touchés à chaque vague significative et laisser le dépôt prêt à être commit sans imposer de commit.
- [x] ADR 009 checkpoint: update affected Logics docs during each meaningful wave and leave the repo commit-ready.
- [x] Keep commit creation under operator control; do not force one commit per micro-step.
- [x] GATE: do not close until lint, audit, and scaffold validation pass.

# Backlog
- `item_081_rendre_l_etat_de_l_analyse_continu_et_exact_apres_rafraichissement`
- `item_082_recomposer_la_navigation_et_le_brief_html_en_espace_desktop_a_deux_colonnes`
- `item_083_expliquer_les_claims_par_une_synthese_scientifique_sourcee`
- `item_084_respecter_les_cooldowns_semantic_scholar_avant_de_signaler_une_erreur_provider`

# Definition of Done (DoD)
- [x] Generated request, product, backlog, and task docs are present.
- [x] Context-pack handoff is available when requested.
- [x] Validation passes.
- [x] Meaningful waves followed ADR 009: affected docs updated and the repo left commit-ready without automatic commits.

# AC Traceability
- request-AC1 -> item_082. Proof: `_nav` renders the version chip and the Recent analyses link; the archive card moved to `/history` (`render_history_page`).
- request-AC2 -> item_081. Proof: the stepper renders outside the disclosure; Step/Status/Details/Output stay in one `details.diagnostic`; Background actions and the transcript preview are gone.
- request-AC3 -> item_081. Proof: `reconcile_run_state` settles stale runs on every read path, covered by the reload and polling tests.
- request-AC4 -> item_082. Proof: `render_brief_html` renders semantic HTML in `.workspace-brief`, two columns above 1080px, with technical details last.
- request-AC5 -> item_083. Proof: every claim leads with a `Signals:` line rendered as labelled pills, followed by the sourced synthesis paragraph.
- request-AC6 -> item_084. Proof: `_await_cooldown` waits out a known cooldown, retries honour retry-after, and recovered limits leave no adapter error.
- request-AC7 -> This task. Proof: `tests/test_analysis_briefs_web.py` and `tests/test_verification.py` cover reload, desktop and mobile rendering, the HTML brief, the claim synthesis, and retry/cooldown.

# Validation
- `.venv/bin/python -m pytest tests/ -q` passes (167 tests).
- `.venv/bin/python -m ruff check .` passes.
- `logics-manager lint --require-status` and `logics-manager audit --group-by-doc` pass.
- pytest 167 passed; ruff check passed; logics lint and audit passed
- Finish workflow executed on 2026-08-02.
- Linked backlog/request close verification passed.

# Report
- Provider resilience: cooldowns are waited out before a request is emitted, 429s are replayed against retry-after within a bounded budget, and a recovered limit no longer reaches the reader as an adapter error. Exhausted retries are reported as a coverage gap instead of a completed check.
- Analysis state: every read path settles the run through `reconcile_run_state`, so a reload after a dead worker shows the terminal status and the brief; abandoned steps become retryable rather than stuck.
- Reading surface: the top bar carries the version and the archive link, the workspace is two columns on desktop, and the brief renders as accessible HTML with technical details at the end.
- Claim explanation: each claim leads with supporting/contradicting/verdict signals as text pills, followed by an LLM synthesis grounded only in the retrieved records, with the caution notes preserved.
- Left uncommitted for the operator to review.
- Finished on 2026-08-02.
- Linked backlog item(s): `item_081_rendre_l_etat_de_l_analyse_continu_et_exact_apres_rafraichissement`, `item_082_recomposer_la_navigation_et_le_brief_html_en_espace_desktop_a_deux_colonnes`, `item_083_expliquer_les_claims_par_une_synthese_scientifique_sourcee`, `item_084_respecter_les_cooldowns_semantic_scholar_avant_de_signaler_une_erreur_provider`
- Related request(s): `req_014_rendre_l_analyse_claimlens_lisible_scientifique_et_fiable_en_production`

# AI Context
- Summary: Orchestrer la lisibilité et la fiabilité du brief ClaimLens
- Keywords: scaffolded-task, request-chain-scaffold, orchestration
- Use when: Coordinating implementation of a scaffolded request chain.
- Skip when: Working on one isolated sibling slice.

# Links
- Request: `req_014_rendre_l_analyse_claimlens_lisible_scientifique_et_fiable_en_production`
- Product brief(s): `prod_018_espace_d_analyse_et_brief_scientifique_orientes_lecture`
- Architecture decision(s): (none yet)
