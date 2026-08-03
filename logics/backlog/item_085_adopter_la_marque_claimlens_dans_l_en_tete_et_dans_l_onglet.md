## item_085_adopter_la_marque_claimlens_dans_l_en_tete_et_dans_l_onglet - Adopter la marque ClaimLens dans l'en-tete et dans l'onglet
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Low
> Theme: Brand identity
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- La loupe générique actuelle ne dit ni la vidéo ni la revue des sources, et aucune icône d'onglet n'identifie l'application.

# Scope
- In:
  - Marque unique sur grille 24, réutilisée par l'en-tête et par l'icône d'onglet.
  - Icône d'onglet inline en data URI, sur la tuile en dégradé de marque.
  - Lisibilité vérifiée à seize et trente-deux pixels, en thème clair et sombre.
- Out:
  - Charte graphique complète, déclinaisons sociales, et fichiers statiques servis séparément.

# Acceptance criteria
- AC1: L'en-tête et la page de connexion rendent la marque retenue et plus l'ancienne loupe.
- AC2: Chaque page sert la même marque comme icône d'onglet, inline et sans requête supplémentaire.
- AC3: La marque hérite de la couleur du contexte, seul le triangle de lecture reste rouge.
- AC4: La marque reste lisible aux tailles d'usage réelles sans détail interne perdu.

# AC Traceability
- request-AC1 -> This backlog slice. Proof: `LOGO_MARK` is the lens, play triangle and review check, verified by `test_the_mark_is_the_lens_play_and_review_check`.
- request-AC2 -> This backlog slice. Proof: `test_every_page_carries_the_inline_tab_icon` checks the inline data-URI icon on the process, history and login pages.
- request-AC7 -> This backlog slice. Proof: brand and tab-icon coverage in `tests/test_analysis_briefs_web.py`.
- request-AC3 -> This backlog slice. Evidence needed: Les claims sont systématiquement traduits en anglais avant toute interrogation de PubMed et Semantic Scholar, quelle que soit la langue de la vidéo.
- request-AC4 -> This backlog slice. Evidence needed: Le brief continue d'afficher le claim dans la langue d'origine; la traduction ne sert que la recherche et le jugement des sources.
- request-AC5 -> This backlog slice. Evidence needed: La prose destinée au lecteur, rationales de sources et synthèse par claim, suit la langue du rapport et non celle des articles.
- request-AC6 -> This backlog slice. Evidence needed: Une traduction indisponible dégrade la recherche sans faire échouer la vérification, et l'incident est tracé dans les résultats d'adaptateur.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Delivery notes
- `MARK_BODY` in `src/claimlens/web.py` holds the drawing once: `LOGO_MARK` wraps it for the header with `currentColor`, and `FAVICON_SVG` wraps it on the brand gradient tile for the tab.
- The tab icon ships as a URL-encoded data URI in `_page_shell`, so it needs no static route and cannot 404 behind the paulmondou.fr proxy.
- The mark was rendered at 16, 32, 64 and 160 pixels on the tile and on both themes before being adopted; the check clears the handle and the ring at every size.

# Links
- Product brief(s): `prod_019_marque_claimlens_et_recherche_scientifique_independante_de_la_langue`
- Architecture decision(s): (none yet)
- Request: `req_015_donner_a_claimlens_sa_marque_propre_et_une_recherche_scientifique_independante_de_la_langue`
- Primary task(s): `task_019_livrer_la_marque_claimlens_et_la_recherche_scientifique_multilingue`

# AI Context
- Summary: Adopter la marque ClaimLens dans l'en-tete et dans l'onglet
- Keywords: scaffolded-backlog, adopter la marque claimlens dans l'en-tete et dans l'onglet, implementation-ready
- Use when: Implementing the scaffolded slice for Adopter la marque ClaimLens dans l'en-tete et dans l'onglet.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.

# Tasks
- `task_019_livrer_la_marque_claimlens_et_la_recherche_scientifique_multilingue`

# Notes
- Task `task_019_livrer_la_marque_claimlens_et_la_recherche_scientifique_multilingue` was finished via `logics-manager flow finish task` on 2026-08-03.
