## task_020_orchestrer_la_finalisation_de_l_espace_d_analyse_claimlens - Orchestrer la finalisation de l'espace d'analyse ClaimLens
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
- [x] 1. Cartographier les routes, sorties et états de run existants, puis décider le contrat de masquage persistant.
- [x] 2. Extraire et tester le client de suivi compatible CSP avant de modifier les interactions de l'espace de travail.
- [x] 3. Livrer les simplifications visuelles et le retrait du champ de langue.
- [x] 4. Ajouter les lecteurs et exports autorisés de transcript et brief HTML.
- [x] 5. Ajouter le cycle close/reopen, les tests d'autorisations et le test navigateur de la chaîne complète.
- [x] 6. Déployer la configuration Caddy cohérente, vérifier les en-têtes publics et consigner les preuves de validation.
- [x] ADR 009 checkpoint: update affected Logics docs during each meaningful wave and leave the repo commit-ready.
- [x] Keep commit creation under operator control; do not force one commit per micro-step.
- [x] GATE: do not close until lint, audit, and scaffold validation pass.

# Backlog
- `item_087_rendre_le_suivi_d_analyse_compatible_csp_et_observable`
- `item_088_simplifier_le_bandeau_et_le_lancement_d_analyse`
- `item_089_fournir_les_transcripts_et_briefs_comme_livrables_lisibles`
- `item_090_masquer_et_reouvrir_les_analyses_terminees`

# Definition of Done (DoD)
- [x] Generated request, product, backlog, and task docs are present.
- [x] Context-pack handoff is available when requested.
- [x] Validation passes.
- [x] Meaningful waves followed ADR 009: affected docs updated and the repo left commit-ready without automatic commits.

# AC Traceability
- request-AC1, request-AC7 -> `item_087_rendre_le_suivi_d_analyse_compatible_csp_et_observable`. Proof: `tests/test_workspace_deliverables.py::test_no_page_needs_more_than_the_production_csp_allows`, `::test_the_client_itself_polls_paints_announces_and_recovers`, `::test_live_client_is_served_same_origin_as_javascript`.
- request-AC2, request-AC6 -> `item_088_simplifier_le_bandeau_et_le_lancement_d_analyse`. Proof: `tests/test_workspace_deliverables.py::test_the_brand_mark_is_eighty_percent_larger`, `::test_the_launcher_no_longer_asks_for_a_report_language`, `::test_a_new_analysis_uses_the_configured_report_language`.
- request-AC3, request-AC5, request-AC7 -> `item_089_fournir_les_transcripts_et_briefs_comme_livrables_lisibles`. Proof: `tests/test_workspace_deliverables.py::test_outputs_offer_readable_links_and_no_server_path`, `::test_transcript_access_separates_missing_from_not_yours`, `::test_transcript_download_is_plain_text_and_authorized`, `::test_the_html_export_is_a_self_contained_document`, `::test_brief_download_serves_html_or_markdown_on_request`.
- request-AC4, request-AC7 -> `item_090_masquer_et_reouvrir_les_analyses_terminees`. Proof: `tests/test_workspace_deliverables.py::test_closing_hides_the_workspace_and_keeps_everything`, `::test_recent_analyses_keeps_a_closed_run_and_offers_to_reopen_it`, `::test_reopening_brings_the_result_back_to_the_workspace`, `::test_close_and_reopen_over_http_respect_ownership`, `::test_closing_a_running_analysis_is_refused_over_http`.

# Validation
- (no validation recorded yet)
- pytest passed on 2026-08-03: 204 passed (dont 24 nouveaux tests de l'espace d'analyse)
- ruff check src tests passed on 2026-08-03: All checks passed
- caddy validate --config Caddyfile passed on 2026-08-03: Valid configuration; caddy adapt confirme script-src 'self' sans unsafe-inline et header_up X-Real-IP pour le site ClaimLens
- balayage CSP HTTP de toutes les pages passed on 2026-08-03: aucun script inline, aucun gestionnaire inline, aucune ressource hors origine
- Finish workflow executed on 2026-08-03.
- Linked backlog/request close verification passed.

# Report
- Le client de suivi est extrait dans `src/claimlens/assets.py` et servi par `/static/live-status.js`; la page ne transporte plus aucun script inline et configure le client par attributs `data-*`.
- Le balayage CSP de toutes les pages a révélé un `onchange="this.form.submit()"` sur `/history`, invisible aux tests existants et bloqué par `script-src 'self'`. Le filtre utilise désormais un bouton Filter, sans JavaScript.
- Le rythme actif ne dépend plus des seuls jobs: le client reste rapide tant que la signature change, ce qui couvre la bascule entre deux jobs sans déclarer active une analyse en attente d'une clé.
- Le transcript nettoyé et le brief sont lus et exportés par des routes autorisées (`/transcript`, `/transcript/download`, `/brief/download?format=html`); aucun chemin serveur n'est présenté comme action, et la colonne Output des détails d'exécution n'affiche plus que le nom de l'artefact.
- Le cycle close/reopen s'appuie sur `pipeline_runs.closed_at` (schéma 8, colonne additive et nullable): fermer masque, ne supprime rien, et refuse une chaîne encore active ou en attente d'entrée utilisateur.
- Côté infra, le site ClaimLens de `/home/paul/dev/paulmondou-infra/Caddyfile` importe maintenant `default_csp` (`script-src 'self'`, sans exception) et pose `header_up X-Real-IP {remote_host}`, qui manquait alors que la documentation de déploiement le supposait. Le déploiement reste à la main de l'opérateur.
- Non livré: aucune vérification dans un vrai navigateur, faute de navigateur dans l'environnement. Le client est exécuté sur un DOM minimal via `tests/live_status_harness.js` (ignoré si `node` est absent) et la conformité CSP est vérifiée par balayage HTTP de toutes les pages.
- Finished on 2026-08-03.
- Linked backlog item(s): `item_087_rendre_le_suivi_d_analyse_compatible_csp_et_observable`, `item_088_simplifier_le_bandeau_et_le_lancement_d_analyse`, `item_089_fournir_les_transcripts_et_briefs_comme_livrables_lisibles`, `item_090_masquer_et_reouvrir_les_analyses_terminees`
- Related request(s): `req_016_finaliser_l_espace_d_analyse_claimlens_et_ses_livrables_lisibles`

# AI Context
- Summary: Orchestrer la finalisation de l'espace d'analyse ClaimLens
- Keywords: scaffolded-task, request-chain-scaffold, orchestration
- Use when: Coordinating implementation of a scaffolded request chain.
- Skip when: Working on one isolated sibling slice.

# Links
- Request: `req_016_finaliser_l_espace_d_analyse_claimlens_et_ses_livrables_lisibles`
- Product brief(s): `prod_020_espace_d_analyse_termine_reouvrable_et_lisible`
- Architecture decision(s): (none yet)
