## item_088_simplifier_le_bandeau_et_le_lancement_d_analyse - Simplifier le bandeau et le lancement d'analyse
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Low
> Theme: interface
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- La marque est trop discrète et le champ Report language ajoute un choix non nécessaire.

# Scope
- In:
  - Augmenter de 80 % les dimensions de l'icône de la navigation principale et ajuster le layout responsive.
  - Retirer Report language de l'UI, de son POST et des textes associés.
  - Documenter et tester l'emploi de la langue configurée par défaut.
- Out:
  - Modifier la configuration globale de langue ou les langues déjà stockées des analyses passées.

# Acceptance criteria
- AC1: L'icône du bandeau est 1,8 fois sa taille actuelle et la barre reste utilisable à largeur mobile.
- AC2: Aucun champ Report language n'est rendu ou accepté depuis le formulaire de création.
- AC3: Une nouvelle analyse emploie la valeur de configuration par défaut de report_language.

# AC Traceability
- request-AC2 -> This backlog slice. Proof: `tests/test_workspace_deliverables.py::test_the_brand_mark_is_eighty_percent_larger` (30px -> 54px, barre qui passe à la ligne en largeur mobile).
- request-AC6 -> This backlog slice. Proof: `tests/test_workspace_deliverables.py::test_the_launcher_no_longer_asks_for_a_report_language` et `::test_a_new_analysis_uses_the_configured_report_language` (un POST qui porte encore le champ est ignoré).
- request-AC1 -> This backlog slice. Evidence needed: Une analyse active actualise les cinq étapes, les erreurs et le brief sans rechargement manuel sous la CSP de production stricte.
- request-AC3 -> This backlog slice. Evidence needed: Le transcript nettoyé expose un lien autorisé de lecture ou téléchargement, sans afficher ni tenter d'ouvrir le chemin local du serveur.
- request-AC4 -> This backlog slice. Evidence needed: Une analyse terminée peut être masquée depuis l'espace de travail, reste disponible dans Recent analyses et peut être rouverte avec son résultat.
- request-AC5 -> This backlog slice. Evidence needed: Un brief terminé est lisible dans le navigateur et téléchargeable en HTML autonome, sans nécessiter d'éditeur Markdown.
- request-AC7 -> This backlog slice. Evidence needed: Des tests navigateur ou d'intégration vérifient le rafraîchissement réel sous CSP, les contrôles de visibilité, les autorisations d'accès aux fichiers et les nouveaux exports.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_020_espace_d_analyse_termine_reouvrable_et_lisible`
- Architecture decision(s): (none yet)
- Request: `req_016_finaliser_l_espace_d_analyse_claimlens_et_ses_livrables_lisibles`
- Primary task(s): `task_020_orchestrer_la_finalisation_de_l_espace_d_analyse_claimlens`

# AI Context
- Summary: Simplifier le bandeau et le lancement d'analyse
- Keywords: scaffolded-backlog, simplifier le bandeau et le lancement d'analyse, implementation-ready
- Use when: Implementing the scaffolded slice for Simplifier le bandeau et le lancement d'analyse.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: Medium
- Rationale: Set by scaffold input or defaulted for grooming.

# Tasks
- `task_020_orchestrer_la_finalisation_de_l_espace_d_analyse_claimlens`

# Notes
- Task `task_020_orchestrer_la_finalisation_de_l_espace_d_analyse_claimlens` was finished via `logics-manager flow finish task` on 2026-08-03.
