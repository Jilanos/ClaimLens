## task_019_livrer_la_marque_claimlens_et_la_recherche_scientifique_multilingue - Livrer la marque ClaimLens et la recherche scientifique multilingue
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Medium
> Theme: Implementation delivery
> Reminder: Update status/understanding/confidence/progress and linked request/backlog references when you edit this doc.

# Context
- Orchestrate the scaffolded request chain and keep sibling implementation slices linked.

# Plan
- [x] 1. Dériver la marque retenue de la grille de propositions et la valider par rendu aux tailles d'usage.
- [x] 2. Partager un seul corps de marque entre l'en-tête et l'icône d'onglet inline.
- [x] 3. Ajouter la frontière de traduction des claims et la porter jusqu'aux adaptateurs.
- [x] 4. Séparer la langue du jugement de la langue de la prose destinée au lecteur.
- [x] 5. Couvrir par des tests la marque, l'icône d'onglet, la recherche en anglais et le repli sans traducteur.
- [x] 6. Exécuter les validations Logics et préparer la version avant déploiement.
- [x] 7. ADR 009 checkpoint: mettre à jour les docs Logics touchés et laisser le dépôt prêt à être commit.
- [x] ADR 009 checkpoint: update affected Logics docs during each meaningful wave and leave the repo commit-ready.
- [x] Keep commit creation under operator control; do not force one commit per micro-step.
- [x] GATE: do not close until lint, audit, and scaffold validation pass.

# Backlog
- `item_085_adopter_la_marque_claimlens_dans_l_en_tete_et_dans_l_onglet`
- `item_086_interroger_la_litterature_en_anglais_quelle_que_soit_la_langue_du_claim`

# Definition of Done (DoD)
- [x] Generated request, product, backlog, and task docs are present.
- [x] Context-pack handoff is available when requested.
- [x] Validation passes.
- [x] Meaningful waves followed ADR 009: affected docs updated and the repo left commit-ready without automatic commits.

# AC Traceability
- request-AC1 -> item_085. Proof: `LOGO_MARK` renders the lens, play triangle and review check in the header and on the login page.
- request-AC2 -> item_085. Proof: `_page_shell` serves `FAVICON_DATA_URI`, the same `MARK_BODY` on the brand tile, inline on every page.
- request-AC3 -> item_086. Proof: `SourceQuery.search_text` carries the English claim, and the adapters query it.
- request-AC4 -> item_086. Proof: the brief renders `claim["claim"]`, so the reader keeps the wording that was spoken.
- request-AC5 -> item_086. Proof: `language_instruction` pins grader and synthesizer prose to the report language.
- request-AC6 -> item_086. Proof: a failed translation falls back per claim and is recorded as a `claim_translation` outcome.
- request-AC7 -> This task. Proof: `tests/test_analysis_briefs_web.py` and `tests/test_verification.py` cover the mark, the tab icon, the English search, the fallback and the language alignment.

# Validation
- `.venv/bin/python -m pytest tests/ -q` passes (177 tests).
- `.venv/bin/python -m ruff check .` passes.
- `logics-manager lint --require-status` and `logics-manager audit --group-by-doc` pass.
- The mark was rendered at 16, 32, 64 and 160 pixels, on the brand tile and on both themes, before adoption.
- A live server run in French confirmed the provider is queried in English while the brief stays French.
- pytest 177 passed; ruff check passed; icon rendered at 16/32/64/160; live French run queried providers in English
- Finish workflow executed on 2026-08-03.
- Linked backlog/request close verification passed.

# Report
- Brand: one `MARK_BODY` now feeds both the header mark and an inline data-URI tab icon, so the tab, the header and paulmondou.fr show the same drawing without a static asset.
- Retrieval: claims are translated to English before any provider call, which was the reason a French video returned no science at all on run g9YIYX22XBk.
- Language split: the search and the judgement happen in English because the literature is English; every sentence the reader sees stays in the report language.
- Degradation: a missing or partial translation searches the claim as written and is recorded, rather than failing the verification.
- Finished on 2026-08-03.
- Linked backlog item(s): `item_085_adopter_la_marque_claimlens_dans_l_en_tete_et_dans_l_onglet`, `item_086_interroger_la_litterature_en_anglais_quelle_que_soit_la_langue_du_claim`
- Related request(s): `req_015_donner_a_claimlens_sa_marque_propre_et_une_recherche_scientifique_independante_de_la_langue`

# AI Context
- Summary: Livrer la marque ClaimLens et la recherche scientifique multilingue
- Keywords: scaffolded-task, request-chain-scaffold, orchestration
- Use when: Coordinating implementation of a scaffolded request chain.
- Skip when: Working on one isolated sibling slice.

# Links
- Request: `req_015_donner_a_claimlens_sa_marque_propre_et_une_recherche_scientifique_independante_de_la_langue`
- Product brief(s): `prod_019_marque_claimlens_et_recherche_scientifique_independante_de_la_langue`
- Architecture decision(s): (none yet)
