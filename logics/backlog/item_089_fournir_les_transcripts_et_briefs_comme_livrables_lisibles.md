## item_089_fournir_les_transcripts_et_briefs_comme_livrables_lisibles - Fournir les transcripts et briefs comme livrables lisibles
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Medium
> Theme: deliverables
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- Les chemins /data sont inutilisables dans le navigateur et le téléchargement .md impose un lecteur technique.

# Scope
- In:
  - Créer des routes autorisées par run pour consulter et télécharger le transcript nettoyé.
  - Rendre ou exporter un brief HTML autonome avec styles de lecture et impression.
  - Remplacer les liens de sortie techniques par des libellés orientés lecteur.
  - Tester les permissions utilisateur et invité ainsi que les réponses 404/403.
- Out:
  - Donner au navigateur un accès à des répertoires ou chemins de fichiers serveur.

# Acceptance criteria
- AC1: La sortie transcript présente un lien Read transcript et/ou Download transcript autorisé pour le run concerné.
- AC2: Le brief est consultable dans l'app et Download HTML produit un document autonome lisible dans un navigateur.
- AC3: Aucun chemin absolu /data n'est présenté comme action utilisateur.

# AC Traceability
- request-AC3 -> This backlog slice. Proof: `tests/test_workspace_deliverables.py::test_outputs_offer_readable_links_and_no_server_path`, `::test_the_transcript_page_reads_the_stored_text`, `::test_transcript_download_is_plain_text_and_authorized`.
- request-AC5 -> This backlog slice. Proof: `tests/test_workspace_deliverables.py::test_the_html_export_is_a_self_contained_document` et `::test_brief_download_serves_html_or_markdown_on_request`.
- request-AC7 -> This backlog slice. Proof: `tests/test_workspace_deliverables.py::test_outputs_offer_readable_links_and_no_server_path` (aucun `/data/outputs` ni chemin absolu dans la page) et `::test_transcript_access_separates_missing_from_not_yours` (403 / 404).
- request-AC1 -> This backlog slice. Evidence needed: Une analyse active actualise les cinq étapes, les erreurs et le brief sans rechargement manuel sous la CSP de production stricte.
- request-AC2 -> This backlog slice. Evidence needed: L'icône ClaimLens du bandeau supérieur est 80 % plus grande sans casser l'alignement ou la navigation mobile.
- request-AC4 -> This backlog slice. Evidence needed: Une analyse terminée peut être masquée depuis l'espace de travail, reste disponible dans Recent analyses et peut être rouverte avec son résultat.
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
- Summary: Fournir les transcripts et briefs comme livrables lisibles
- Keywords: scaffolded-backlog, fournir les transcripts et briefs comme livrables lisibles, implementation-ready
- Use when: Implementing the scaffolded slice for Fournir les transcripts et briefs comme livrables lisibles.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.

# Tasks
- `task_020_orchestrer_la_finalisation_de_l_espace_d_analyse_claimlens`

# Notes
- Task `task_020_orchestrer_la_finalisation_de_l_espace_d_analyse_claimlens` was finished via `logics-manager flow finish task` on 2026-08-03.
