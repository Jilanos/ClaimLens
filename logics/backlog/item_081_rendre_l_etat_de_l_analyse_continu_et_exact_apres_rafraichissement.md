## item_081_rendre_l_etat_de_l_analyse_continu_et_exact_apres_rafraichissement - Rendre l'état de l'analyse continu et exact après rafraîchissement
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Medium
> Theme: Analysis progress UX
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- La progression détaillée est cachée ou parasitée par des actions de fond inutiles.
- Un rafraîchissement peut laisser l'utilisateur sur un état de job périmé alors que l'analyse est terminée.

# Scope
- In:
  - Chaîne d'étapes métier toujours visible pendant le run.
  - Panneau dépliable pour Step, Status, Details et Output.
  - Suppression des zones Background actions et Cleaned transcript preview.
  - Réconciliation du job et du résultat au chargement, au polling et à la transition terminale.
- Out:
  - Refonte du moteur de traitement ou du modèle de jobs.

# Acceptance criteria
- AC1: La timeline métier reste visible sans interaction pendant un run actif.
- AC2: Les diagnostics sont consultables dans un seul panneau repliable et ne masquent jamais la timeline.
- AC3: Recharger pendant ou après un run affiche l'état serveur le plus récent et le résultat lorsqu'il existe.
- AC4: Les vues supprimées ne sont plus rendues ni annoncées aux lecteurs d'écran.

# AC Traceability
- request-AC2 -> This backlog slice. Proof: the stepper renders outside `details.diagnostic`, verified by `test_the_step_timeline_is_visible_without_opening_anything`.
- request-AC3 -> This backlog slice. Proof: `reconcile_run_state` settles the run on every read path, verified by `test_a_reload_settles_a_run_the_worker_finished_without_saying_so` and `test_polling_and_reloading_report_the_same_settled_state`.
- request-AC7 -> This backlog slice. Proof: refresh-state coverage in `tests/test_analysis_briefs_web.py`, including `test_a_reload_makes_an_abandoned_step_retryable_instead_of_stuck`.
- request-AC1 -> This backlog slice. Evidence needed: L'en-tête de l'application affiche le numéro de version courant et inclut un accès Recent analyses dans la barre supérieure ; cet accès n'est plus présenté sous l'espace de travail.
- request-AC4 -> This backlog slice. Evidence needed: Une analyse terminée affiche directement un brief HTML accessible et mis en page. Sur écran desktop, le brief exploite une colonne droite de la vue à deux colonnes ; le titre ClaimLens et le titre de la vidéo sont visuellement distincts, et les métadonnées techniques sont en bas du brief.
- request-AC5 -> This backlog slice. Evidence needed: Chaque checked claim présente d'abord un résumé compact et non décoratif des signaux supporting, contradicting et du verdict, suivi d'un texte LLM sourcé expliquant ce que la recherche voisine indique, y compris lorsque le verdict demeure unclear.
- request-AC6 -> This backlog slice. Evidence needed: Les appels Semantic Scholar respectent automatiquement retry-after et cooldown, avec attente et retry bornés. Les rate limits transitoires ne sont plus exposées comme Adapter errors dans un résultat normalement récupérable.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Delivery notes
- `reconcile_run_state` in `src/claimlens/web.py` settles a run before every render and every poll: an abandoned step becomes retryable, and a chain that finished without writing its status is closed as succeeded or completed with limits.
- The step timeline renders outside the `Execution details` disclosure, so it is visible without interaction; Step, Status, Details and Output remain inside that single panel.
- Background actions and the cleaned transcript preview are no longer rendered or sent in the live payload.

# Links
- Product brief(s): `prod_018_espace_d_analyse_et_brief_scientifique_orientes_lecture`
- Architecture decision(s): (none yet)
- Request: `req_014_rendre_l_analyse_claimlens_lisible_scientifique_et_fiable_en_production`
- Primary task(s): `task_018_orchestrer_la_lisibilite_et_la_fiabilite_du_brief_claimlens`

# AI Context
- Summary: Rendre l'état de l'analyse continu et exact après rafraîchissement
- Keywords: scaffolded-backlog, rendre l'état de l'analyse continu et exact après rafraîchissement, implementation-ready
- Use when: Implementing the scaffolded slice for Rendre l'état de l'analyse continu et exact après rafraîchissement.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.

# Tasks
- `task_018_orchestrer_la_lisibilite_et_la_fiabilite_du_brief_claimlens`

# Notes
- Task `task_018_orchestrer_la_lisibilite_et_la_fiabilite_du_brief_claimlens` was finished via `logics-manager flow finish task` on 2026-08-02.
