## req_015_donner_a_claimlens_sa_marque_propre_et_une_recherche_scientifique_independante_de_la_langue - Donner a ClaimLens sa marque propre et une recherche scientifique independante de la langue
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Complexity: Medium
> Theme: Brand identity and multilingual evidence retrieval
> Reminder: Update status/understanding/confidence and linked backlog/task references when you edit this doc.

# Needs
- Reconnaître ClaimLens dans un onglet et dans l'en-tête grâce à une marque qui dit vidéo, examen et revue des sources.
- Obtenir des résultats scientifiques même lorsque la vidéo et le rapport sont dans une autre langue que l'anglais.

# Context
- Le run g9YIYX22XBk portait sur une vidéo française: le récapitulatif en français convient à l'utilisateur, mais aucune source n'a été trouvée.
- PubMed et Semantic Scholar indexent en anglais; un claim interrogé tel quel dans une autre langue ne renvoie rien.
- L'icône retenue vient de la grille de propositions et remplace la loupe générique existante.
- L'application est déployée sous paulmondou.fr, où l'icône d'onglet est la première marque visible.

# Acceptance criteria
- AC1: L'en-tête de l'application affiche la marque retenue, combinant loupe, triangle de lecture et coche de revue, à la place de l'ancienne loupe.
- AC2: Chaque page sert une icône d'onglet inline reprenant exactement la même marque sur la tuile de marque, sans requête supplémentaire.
- AC3: Les claims sont systématiquement traduits en anglais avant toute interrogation de PubMed et Semantic Scholar, quelle que soit la langue de la vidéo.
- AC4: Le brief continue d'afficher le claim dans la langue d'origine; la traduction ne sert que la recherche et le jugement des sources.
- AC5: La prose destinée au lecteur, rationales de sources et synthèse par claim, suit la langue du rapport et non celle des articles.
- AC6: Une traduction indisponible dégrade la recherche sans faire échouer la vérification, et l'incident est tracé dans les résultats d'adaptateur.
- AC7: Les tests couvrent la marque, l'icône d'onglet, la recherche en anglais depuis un claim français, le repli sans traducteur et l'alignement de langue.

# Definition of Ready (DoR)
- [x] Problem statement is explicit and user impact is clear.
- [x] Scope boundaries (in/out) are explicit.
- [x] Acceptance criteria are testable.
- [x] Dependencies and known risks are listed.

# Companion docs
- Product brief(s): `prod_019_marque_claimlens_et_recherche_scientifique_independante_de_la_langue`
- Architecture decision(s): (none yet)

# References
- Feedback utilisateur du 2026-08-03 sur le run g9YIYX22XBk
- Grille de 16 propositions d'icônes, concept retenu: loupe, triangle play et coche de revue

# AI Context
- Summary: Donner a ClaimLens sa marque propre et une recherche scientifique independante de la langue
- Keywords: request-chain-scaffold, donner a claimlens sa marque propre et une recherche scientifique independante de la langue, development-ready
- Use when: You need to implement or review the scaffolded workflow for Donner a ClaimLens sa marque propre et une recherche scientifique independante de la langue.
- Skip when: The change is unrelated to this scaffolded request chain.

# Backlog
- `item_085_adopter_la_marque_claimlens_dans_l_en_tete_et_dans_l_onglet`
- `item_086_interroger_la_litterature_en_anglais_quelle_que_soit_la_langue_du_claim`
