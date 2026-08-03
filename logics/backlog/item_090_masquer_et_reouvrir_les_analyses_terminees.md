## item_090_masquer_et_reouvrir_les_analyses_terminees - Masquer et réouvrir les analyses terminées
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Medium
> Theme: workspace-lifecycle
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- Un résultat terminé conserve l'espace Active analysis et Result ouvert, encombrant le flux de travail suivant.

# Scope
- In:
  - Ajouter une action explicite Close analysis pour les runs terminés.
  - Conserver les données, le brief et la traçabilité du run dans l'historique.
  - Permettre de rouvrir un run terminé dans l'espace de travail depuis Recent analyses.
  - Définir la persistance de la préférence de masquage par utilisateur ou invité.
- Out:
  - Supprimer une analyse, son transcript ou son brief.

# Acceptance criteria
- AC1: Close analysis masque l'espace actif et le résultat seulement lorsque toute la chaîne est terminale.
- AC2: Recent analyses permet de rouvrir un run fermé et d'afficher son brief complet.
- AC3: Fermer une analyse ne supprime aucune donnée et ne masque pas les analyses encore en cours.

# AC Traceability
- request-AC4 -> This backlog slice. Proof: `tests/test_workspace_deliverables.py::test_closing_hides_the_workspace_and_keeps_everything`, `::test_an_unfinished_analysis_cannot_be_closed`, `::test_a_run_paused_for_the_user_is_still_working`, `::test_closing_a_running_analysis_is_refused_over_http`.
- request-AC7 -> This backlog slice. Proof: `tests/test_workspace_deliverables.py::test_recent_analyses_keeps_a_closed_run_and_offers_to_reopen_it`, `::test_reopening_brings_the_result_back_to_the_workspace`, `::test_close_and_reopen_over_http_respect_ownership`.
- request-AC1 -> This backlog slice. Evidence needed: Une analyse active actualise les cinq étapes, les erreurs et le brief sans rechargement manuel sous la CSP de production stricte.
- request-AC2 -> This backlog slice. Evidence needed: L'icône ClaimLens du bandeau supérieur est 80 % plus grande sans casser l'alignement ou la navigation mobile.
- request-AC3 -> This backlog slice. Evidence needed: Le transcript nettoyé expose un lien autorisé de lecture ou téléchargement, sans afficher ni tenter d'ouvrir le chemin local du serveur.
- request-AC5 -> This backlog slice. Evidence needed: Un brief terminé est lisible dans le navigateur et téléchargeable en HTML autonome, sans nécessiter d'éditeur Markdown.
- request-AC6 -> This backlog slice. Evidence needed: Le formulaire de création ne contient plus Report language et les analyses nouvelles utilisent la langue de rapport configurée par défaut.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_020_espace_d_analyse_termine_reouvrable_et_lisible`
- Architecture decision(s): (none yet)
- Request: `req_016_finaliser_l_espace_d_analyse_claimlens_et_ses_livrables_lisibles`
- Primary task(s): `task_020_orchestrer_la_finalisation_de_l_espace_d_analyse_claimlens`

# AI Context
- Summary: Masquer et réouvrir les analyses terminées
- Keywords: scaffolded-backlog, masquer et réouvrir les analyses terminées, implementation-ready
- Use when: Implementing the scaffolded slice for Masquer et réouvrir les analyses terminées.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: Medium
- Rationale: Set by scaffold input or defaulted for grooming.

# Tasks
- `task_020_orchestrer_la_finalisation_de_l_espace_d_analyse_claimlens`

# Notes
- Task `task_020_orchestrer_la_finalisation_de_l_espace_d_analyse_claimlens` was finished via `logics-manager flow finish task` on 2026-08-03.
