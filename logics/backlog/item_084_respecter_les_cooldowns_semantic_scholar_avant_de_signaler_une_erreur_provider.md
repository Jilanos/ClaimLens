## item_084_respecter_les_cooldowns_semantic_scholar_avant_de_signaler_une_erreur_provider - Respecter les cooldowns Semantic Scholar avant de signaler une erreur provider
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Medium
> Theme: Provider resilience
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- Les cooldowns et HTTP 429 Semantic Scholar deviennent des Adapter errors visibles, malgré un délai de reprise connu.

# Scope
- In:
  - Lecture de retry-after et cooldown provider.
  - Attente asynchrone, retry borné et observabilité des tentatives.
  - Distinction entre limite temporaire récupérée et erreur définitive dans le résultat utilisateur.
- Out:
  - Contourner les quotas provider, augmenter le quota, ou masquer un échec final non récupérable.

# Acceptance criteria
- AC1: Un cooldown explicite retarde la prochaine requête avant son émission.
- AC2: Une réponse 429 avec retry-after est rejouée dans une limite configurable et testée sans attente réelle.
- AC3: Une reprise réussie ne laisse aucun Adapter error de rate limit dans le rapport final.
- AC4: Après épuisement des tentatives, le résultat explique la limite durable sans prétendre à une vérification complète.

# AC Traceability
- request-AC6 -> This backlog slice. Proof: `test_an_explicit_cooldown_delays_the_next_request_instead_of_skipping_it`, `test_retry_after_is_honoured_within_a_bounded_number_of_replays` and `test_a_recovered_rate_limit_leaves_no_provider_error_in_the_report`.
- request-AC7 -> This backlog slice. Proof: retry and cooldown behaviour is exercised without real waiting through the `_sleep` boundary, including `test_exhausted_retries_explain_the_limit_without_claiming_full_coverage`.
- request-AC1 -> This backlog slice. Evidence needed: L'en-tête de l'application affiche le numéro de version courant et inclut un accès Recent analyses dans la barre supérieure ; cet accès n'est plus présenté sous l'espace de travail.
- request-AC2 -> This backlog slice. Evidence needed: Pendant toute analyse non terminale, la chaîne complète des étapes métier est visible en permanence. Les données Step, Status, Details et Output sont placées dans un panneau dépliable ; Background actions et Cleaned transcript preview ne sont plus visibles dans l'interface.
- request-AC3 -> This backlog slice. Evidence needed: Après un rechargement de page, l'interface récupère et affiche sans état périmé le statut terminal, les étapes terminées et les résultats du dernier run concerné.
- request-AC4 -> This backlog slice. Evidence needed: Une analyse terminée affiche directement un brief HTML accessible et mis en page. Sur écran desktop, le brief exploite une colonne droite de la vue à deux colonnes ; le titre ClaimLens et le titre de la vidéo sont visuellement distincts, et les métadonnées techniques sont en bas du brief.
- request-AC5 -> This backlog slice. Evidence needed: Chaque checked claim présente d'abord un résumé compact et non décoratif des signaux supporting, contradicting et du verdict, suivi d'un texte LLM sourcé expliquant ce que la recherche voisine indique, y compris lorsque le verdict demeure unclear.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Delivery notes
- `_await_cooldown` waits out a known provider cooldown before the request is emitted, up to `COOLDOWN_MAX_WAIT_SECONDS`; a longer cooldown is reported as a durable limit instead of a silent skip.
- Retries honour retry-after within `SEARCH_RETRY_ATTEMPTS`, and `_sleep` is the single waiting boundary so tests exercise the behaviour without real delay.
- A recovered limit leaves no adapter error in the report; an exhausted one is reported as a coverage gap that does not claim a complete check.

# Links
- Product brief(s): `prod_018_espace_d_analyse_et_brief_scientifique_orientes_lecture`
- Architecture decision(s): (none yet)
- Request: `req_014_rendre_l_analyse_claimlens_lisible_scientifique_et_fiable_en_production`
- Primary task(s): `task_018_orchestrer_la_lisibilite_et_la_fiabilite_du_brief_claimlens`

# AI Context
- Summary: Respecter les cooldowns Semantic Scholar avant de signaler une erreur provider
- Keywords: scaffolded-backlog, respecter les cooldowns semantic scholar avant de signaler une erreur provider, implementation-ready
- Use when: Implementing the scaffolded slice for Respecter les cooldowns Semantic Scholar avant de signaler une erreur provider.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.

# Tasks
- `task_018_orchestrer_la_lisibilite_et_la_fiabilite_du_brief_claimlens`

# Notes
- Task `task_018_orchestrer_la_lisibilite_et_la_fiabilite_du_brief_claimlens` was finished via `logics-manager flow finish task` on 2026-08-02.
