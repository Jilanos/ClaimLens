## task_028_remplacer_les_assets_claimlens_par_les_masters_icones_v3_corriges - Remplacer les assets ClaimLens par les masters Icones V3 corriges
> From version: 1.0.0
> Schema version: 1.0
> Status: Ready
> Understanding: 90%
> Confidence: 85%
> Progress: 0%
> Complexity: Medium
> Theme: Implementation delivery
> Reminder: Update status/understanding/confidence/progress and linked request/backlog references when you edit this doc.

# Context
- Orchestrate the scaffolded request chain and keep sibling implementation slices linked.

# Plan
- [ ] 1. Copier les cinq masters dans `src/claimlens/static/`.
- [ ] 2. Refondre `assets.py` en accesseurs PNG par variante.
- [ ] 3. Adapter les routes et le HTML de `web.py` pour la bascule par media query.
- [ ] 4. Retirer les SVG orphelins puis verifier le rendu dans les deux themes.
- [ ] 5. Preparer la version `1.8.3` -> `1.8.4` dans `pyproject.toml` et `src/claimlens/__init__.py`.
- [ ] 6. Committer `Prepare ... v1.8.4`, pousser sur `main` et attendre le CI vert sur ce commit.
- [ ] 7. Creer et pousser le tag annote `v1.8.4`, puis verifier les quatre jobs du workflow release.
- [ ] 8. Consigner SHA, tag et URL du run dans le closeout.
- [ ] ADR 009 checkpoint: update affected Logics docs during each meaningful wave and leave the repo commit-ready.
- [ ] Keep commit creation under operator control; do not force one commit per micro-step.
- [ ] GATE: do not close until lint, audit, and scaffold validation pass.

# Backlog
- `item_104_servir_les_masters_claimlens_en_png_dark_et_light`
- `item_105_publier_la_version_1_8_4_apres_remplacement_des_assets`

# Definition of Done (DoD)
- [ ] Generated request, product, backlog, and task docs are present.
- [ ] Context-pack handoff is available when requested.
- [ ] Validation passes.
- [ ] Meaningful waves followed ADR 009: affected docs updated and the repo left commit-ready without automatic commits.

# AC Traceability
- request-AC1, request-AC2, request-AC3, request-AC4 -> `item_104_servir_les_masters_claimlens_en_png_dark_et_light`. Proof deferred to slice closeout.
- request-AC5 -> `item_105_publier_la_version_1_8_4_apres_remplacement_des_assets`. Proof deferred to slice closeout.

# Validation
- (no validation recorded yet)

# Report
- Not started.

# AI Context
- Summary: Remplacer les assets ClaimLens par les masters Icones V3 corriges
- Keywords: scaffolded-task, request-chain-scaffold, orchestration
- Use when: Coordinating implementation of a scaffolded request chain.
- Skip when: Working on one isolated sibling slice.

# Links
- Request: `req_024_remplacer_les_assets_claimlens_par_les_masters_icones_v3_corriges`
- Product brief(s): `prod_027_identite_claimlens_alignee_sur_icones_v3_corrige`
- Architecture decision(s): (none yet)
