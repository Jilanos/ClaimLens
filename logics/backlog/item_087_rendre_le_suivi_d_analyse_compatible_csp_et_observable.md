## item_087_rendre_le_suivi_d_analyse_compatible_csp_et_observable - Rendre le suivi d'analyse compatible CSP et observable
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Medium
> Theme: live-progress
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- Le polling est injecté dans un script inline que la CSP de production bloque.
- Un échec de polling est silencieux et une courte transition entre jobs peut provoquer un backoff inutile.

# Scope
- In:
  - Extraire le client de polling dans un asset servi en same-origin.
  - Passer la configuration de run par attributs data sûrs.
  - Préserver CSP script-src 'self' sans unsafe-inline.
  - Afficher un état de connexion et calculer l'activité à partir du run et des jobs.
  - Ajouter une vérification navigateur ou HTTP+JS sous CSP.
- Out:
  - Passage à WebSocket ou SSE.

# Acceptance criteria
- AC1: Le navigateur exécute le client de suivi avec la CSP script-src 'self' et rafraîchit chaque changement de step.
- AC2: Après des erreurs répétées de polling, l'interface annonce que les mises à jour sont indisponibles puis se rétablit automatiquement.
- AC3: Une transition entre deux jobs ne dégrade pas le rythme actif à 15 secondes.

# AC Traceability
- request-AC1 -> This backlog slice. Proof: `tests/test_workspace_deliverables.py::test_no_page_needs_more_than_the_production_csp_allows` et `::test_the_client_itself_polls_paints_announces_and_recovers` (le client est exécuté et repeint la région à chaque changement de signature).
- request-AC7 -> This backlog slice. Proof: `tests/test_workspace_deliverables.py::test_the_client_itself_polls_paints_announces_and_recovers` (annonce après deux échecs consécutifs, notice retirée au premier succès).
- request-AC2 -> This backlog slice. Evidence needed: L'icône ClaimLens du bandeau supérieur est 80 % plus grande sans casser l'alignement ou la navigation mobile.
- request-AC3 -> This backlog slice. Evidence needed: Le transcript nettoyé expose un lien autorisé de lecture ou téléchargement, sans afficher ni tenter d'ouvrir le chemin local du serveur.
- request-AC4 -> This backlog slice. Evidence needed: Une analyse terminée peut être masquée depuis l'espace de travail, reste disponible dans Recent analyses et peut être rouverte avec son résultat.
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
- Summary: Rendre le suivi d'analyse compatible CSP et observable
- Keywords: scaffolded-backlog, rendre le suivi d'analyse compatible csp et observable, implementation-ready
- Use when: Implementing the scaffolded slice for Rendre le suivi d'analyse compatible CSP et observable.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.

# Tasks
- `task_020_orchestrer_la_finalisation_de_l_espace_d_analyse_claimlens`

# Notes
- Task `task_020_orchestrer_la_finalisation_de_l_espace_d_analyse_claimlens` was finished via `logics-manager flow finish task` on 2026-08-03.
