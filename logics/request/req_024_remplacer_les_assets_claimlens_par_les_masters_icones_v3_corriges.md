## req_024_remplacer_les_assets_claimlens_par_les_masters_icones_v3_corriges - Remplacer les assets ClaimLens par les masters Icones V3 corriges
> From version: 1.0.0
> Schema version: 1.0
> Status: Draft
> Understanding: 90%
> Confidence: 85%
> Complexity: High
> Theme: Brand asset integration
> Reminder: Update status/understanding/confidence and linked backlog/task references when you edit this doc.

# Needs
- Remplacer l'icone et l'embleme SVG par les masters PNG dark et light, et exploiter la bascule de theme deja presente.

# Context
- Les masters approuves sont dans `WORK/perso/Icones V3`, tous en PNG RGBA 1024x1024.
- Le suffixe de variante designe le contour: `-dark` porte un lisere pale et se pose sur fond sombre, `-light` porte un contour navy et se pose sur fond clair.
- Le lot Icones V3 precedemment integre reposait sur de mauvaises images: ce corpus corrige la source, pas la demarche.
- Certaines marques n'ont qu'un ou deux masters (Gnosis, Paul Mondou, Kapsule, F1 Datas). Consigne operateur: reutiliser ce master unique pour l'embleme comme pour l'icone.
- Les quatorze masters sont a fond transparent: coins a alpha=0 et 28% a 87% de pixels transparents selon l'asset. Consigne operateur: ne rien ajouter derriere, ni en favicon ni en embleme.
- Politique de taille arretee avec l'operateur: tuiles et icones de service en 256 px, emblemes en 512 px, favicons en 128 px, icones PWA en 192 et 512 px, ICO multi-tailles 16/32/48/64/128/256. Les masters 1024 px restent la source, jamais l'asset servi.
- ClaimLens sert une UI claire et une UI sombre via `@media (prefers-color-scheme: dark)` dans `web.py`.
- Les quatre masters ClaimLens permettent enfin de servir la bonne variante par theme, ce que le SVG unique actuel ne fait pas.
- `assets.py` expose des accesseurs typés SVG (`claimlens_icon_svg`, `claimlens_emblem_svg`): le passage au PNG impose de renommer ces fonctions, d'ajuster les types MIME et les routes de `web.py`.

# Acceptance criteria
- AC1: Chaque fichier livre est un derive fidele du master Icones V3 correspondant, reduit par moyenne d'aire ponderee par l'alpha a la taille d'usage declaree, sans perte de transparence.
- AC2: Aucune reference d'asset n'est cassee apres remplacement, extensions et types MIME inclus.
- AC3: Le rendu est verifie visuellement sur le theme reellement servi par l'application.
- AC4: La transparence des masters est preservee: aucun fond, plaque ou cartouche n'est ajoute derriere l'asset, favicon et embleme compris.
- AC5: La livraison se termine par un commit de version X.Y.Z+1, un push, puis un tag annote vX.Y.Z+1 dont le workflow release est vert.

# Definition of Ready (DoR)
- [x] Problem statement is explicit and user impact is clear.
- [x] Scope boundaries (in/out) are explicit.
- [x] Acceptance criteria are testable.
- [x] Dependencies and known risks are listed.

# Companion docs
- Product brief(s): `prod_027_identite_claimlens_alignee_sur_icones_v3_corrige`
- Architecture decision(s): (none yet)

# References
- WORK/perso/Icones V3/

# AI Context
- Summary: Remplacer les assets ClaimLens par les masters Icones V3 corriges
- Keywords: request-chain-scaffold, remplacer les assets claimlens par les masters icones v3 corriges, development-ready
- Use when: You need to implement or review the scaffolded workflow for Remplacer les assets ClaimLens par les masters Icones V3 corriges.
- Skip when: The change is unrelated to this scaffolded request chain.

# Backlog
- `item_104_servir_les_masters_claimlens_en_png_dark_et_light`
- `item_105_publier_la_version_1_8_4_apres_remplacement_des_assets`
