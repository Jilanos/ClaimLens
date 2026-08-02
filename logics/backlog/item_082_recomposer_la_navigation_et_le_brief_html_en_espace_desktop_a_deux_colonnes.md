## item_082_recomposer_la_navigation_et_le_brief_html_en_espace_desktop_a_deux_colonnes - Recomposer la navigation et le brief HTML en espace desktop à deux colonnes
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: High
> Theme: Results presentation
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- La largeur desktop est sous-exploitée et le brief Markdown rend le résultat peu lisible.
- Les accès et métadonnées ne suivent pas la hiérarchie de lecture attendue.

# Scope
- In:
  - Version et Recent analyses dans la barre supérieure.
  - Disposition desktop à deux colonnes avec brief dans la colonne droite.
  - Brief HTML sémantique, accessible et responsive affiché immédiatement après succès.
  - Distinction visuelle entre ClaimLens et le titre vidéo ; métadonnées techniques placées en fin de brief.
- Out:
  - Export PDF, partage externe et refonte de l'identité de marque.

# Acceptance criteria
- AC1: L'en-tête contient la version et Recent analyses, y compris au clavier et sur mobile.
- AC2: À une largeur desktop définie par les tests, l'espace actif et le brief occupent deux colonnes lisibles sans défilement horizontal.
- AC3: Le résultat n'est pas présenté comme du Markdown brut et conserve une structure HTML sémantique.
- AC4: Les métadonnées techniques suivent le contenu éditorial du brief et le titre produit reste distinct du titre vidéo.

# AC Traceability
- request-AC1 -> This backlog slice. Proof: `test_the_top_bar_carries_the_version_and_the_archive_link` and `test_the_top_bar_stays_usable_on_a_phone_and_by_keyboard`.
- request-AC4 -> This backlog slice. Proof: `test_the_workspace_puts_the_brief_in_a_second_desktop_column`, `test_the_brief_is_rendered_as_html_and_never_as_raw_markdown` and `test_technical_metadata_follows_the_editorial_content_of_the_brief`.
- request-AC7 -> This backlog slice. Proof: desktop, mobile and HTML-brief rendering coverage in `tests/test_analysis_briefs_web.py`.
- request-AC2 -> This backlog slice. Evidence needed: Pendant toute analyse non terminale, la chaîne complète des étapes métier est visible en permanence. Les données Step, Status, Details et Output sont placées dans un panneau dépliable ; Background actions et Cleaned transcript preview ne sont plus visibles dans l'interface.
- request-AC3 -> This backlog slice. Evidence needed: Après un rechargement de page, l'interface récupère et affiche sans état périmé le statut terminal, les étapes terminées et les résultats du dernier run concerné.
- request-AC5 -> This backlog slice. Evidence needed: Chaque checked claim présente d'abord un résumé compact et non décoratif des signaux supporting, contradicting et du verdict, suivi d'un texte LLM sourcé expliquant ce que la recherche voisine indique, y compris lorsque le verdict demeure unclear.
- request-AC6 -> This backlog slice. Evidence needed: Les appels Semantic Scholar respectent automatiquement retry-after et cooldown, avec attente et retry bornés. Les rate limits transitoires ne sont plus exposées comme Adapter errors dans un résultat normalement récupérable.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Delivery notes
- The top bar carries the version chip and a `Recent analyses` link; the archive lives at `/history` (`render_history_page`) instead of under the workspace.
- `.workspace` is one column by default and two columns above 1080px, with the brief in the right column and no horizontal scrolling.
- `render_brief_html` turns the stored Markdown into semantic HTML; the product name is a kicker above the video title, and technical details close the brief.

# Links
- Product brief(s): `prod_018_espace_d_analyse_et_brief_scientifique_orientes_lecture`
- Architecture decision(s): (none yet)
- Request: `req_014_rendre_l_analyse_claimlens_lisible_scientifique_et_fiable_en_production`
- Primary task(s): `task_018_orchestrer_la_lisibilite_et_la_fiabilite_du_brief_claimlens`

# AI Context
- Summary: Recomposer la navigation et le brief HTML en espace desktop à deux colonnes
- Keywords: scaffolded-backlog, recomposer la navigation et le brief html en espace desktop à deux colonnes, implementation-ready
- Use when: Implementing the scaffolded slice for Recomposer la navigation et le brief HTML en espace desktop à deux colonnes.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.

# Tasks
- `task_018_orchestrer_la_lisibilite_et_la_fiabilite_du_brief_claimlens`

# Notes
- Task `task_018_orchestrer_la_lisibilite_et_la_fiabilite_du_brief_claimlens` was finished via `logics-manager flow finish task` on 2026-08-02.
