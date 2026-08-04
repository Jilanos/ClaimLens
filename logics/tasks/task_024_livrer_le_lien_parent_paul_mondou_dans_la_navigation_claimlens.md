## task_024_livrer_le_lien_parent_paul_mondou_dans_la_navigation_claimlens - Livrer le lien parent Paul Mondou dans la navigation ClaimLens
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Medium
> Theme: Implementation delivery
> Reminder: Update status/understanding/confidence/progress and linked request/backlog references when you edit this doc.
> Indicators reviewed: 2026-08-04

# Context
- Orchestrate the scaffolded request chain and keep sibling implementation slices linked.

# Plan
- [x] 1. Copier l'emblème transparent source dans l'emplacement d'assets retenu et vérifier son intégration au packaging/container.
- [x] 2. Remplacer .avatar dans _nav par le lien externe accessible, puis ajuster les styles de l'en-tête aux deux tailles d'écran.
- [x] 3. Ajouter ou adapter les tests de rendu de navigation pour les états connecté et invité.
- [x] 4. Exécuter les tests ciblés puis la suite pertinente, et valider le corpus Logics avant handoff.
- [x] ADR 009 checkpoint: update affected Logics docs during each meaningful wave and leave the repo commit-ready.
- [x] Keep commit creation under operator control; do not force one commit per micro-step.
- [x] GATE: do not close until lint, audit, and scaffold validation pass.

# Backlog
- `item_099_remplacer_l_avatar_de_navigation_par_l_embleme_paul_mondou`

# Definition of Done (DoD)
- [x] Generated request, product, backlog, and task docs are present.
- [x] Context-pack handoff is available when requested.
- [x] Validation passes.
- [x] Meaningful waves followed ADR 009: affected docs updated and the repo left commit-ready without automatic commits.

# AC Traceability
- request-AC1 -> `item_099_remplacer_l_avatar_de_navigation_par_l_embleme_paul_mondou`. Proof: `src/claimlens/web.py` `_nav` no longer builds a `.avatar` span nor an initial derived from `context.email`; the `.avatar` rule is gone from `STYLES`. Covered by `tests/test_workspace_deliverables.py::test_signed_in_bar_swaps_the_account_avatar_for_the_parent_link` and `::test_guest_bar_keeps_login_and_offers_the_same_parent_link`.
- request-AC2 -> `item_099_remplacer_l_avatar_de_navigation_par_l_embleme_paul_mondou`. Proof: `_parent_link` in `src/claimlens/web.py` emits a single `.parent-link` inside `.navuser` targeting `https://paulmondou.fr` and loading `/static/paulmondou-emblem.png`, served from `src/claimlens/static/paulmondou-emblem.png` (a versioned copy of `paulmondou-emblem-dark-transparent.png`) through `claimlens.assets.parent_emblem_png`. No runtime path leaves the installed package. Covered by `::test_signed_in_bar_swaps_the_account_avatar_for_the_parent_link` and `::test_the_parent_emblem_is_served_same_origin_with_its_transparency`.
- request-AC3 -> `item_099_remplacer_l_avatar_de_navigation_par_l_embleme_paul_mondou`. Proof: the link carries `aria-label="Visit paulmondou.fr"`, an empty `alt` on the decorative image, and a `:focus-visible` outline matching the navigation style; since v1.8.1 it navigates in the current tab, so it carries neither `target` nor `rel`. `Logout`, the e-mail and the existing links are untouched. Covered by `::test_the_parent_link_navigates_in_place_and_announces_its_destination`.
- request-AC4 -> `item_099_remplacer_l_avatar_de_navigation_par_l_embleme_paul_mondou`. Proof: `STYLES` reserves a 30 px `flex:none` square with `object-fit:contain`, so the PNG keeps its 311x311 ratio and the bar cannot shift on decode; under the existing 720 px breakpoint the e-mail hides while the link stays in place. Covered by `::test_the_parent_link_holds_a_stable_square_at_every_width`.
- request-AC5 -> `item_099_remplacer_l_avatar_de_navigation_par_l_embleme_paul_mondou`. Proof: six tests in `tests/test_workspace_deliverables.py` cover the signed-in and guest markup, the exact link attributes, the reserved square, the bar's single off-origin destination, and the same-origin RGBA PNG response; the CSP sweep in `::test_no_page_needs_more_than_the_production_csp_allows` now names `paulmondou.fr` as a chosen destination rather than a loaded resource, and exercises it for real since the guest bar carries the link. Packaging proof: `hatchling build` places `claimlens/static/paulmondou-emblem.png` in both the wheel and the sdist, and the Dockerfile installs from `src`.

# Amendments
- 2026-08-04, post-closeout, operator decision: the parent link is shown to guests as well, not only to authenticated sessions. `_nav` now appends `_parent_link()` in both branches; `item_099` scope and AC2 were widened to match, and the guest test asserts the link instead of its absence. Deployed CSP allows it unchanged (`img-src 'self' data:` for the same-origin PNG; the link is a destination, not a loaded resource). Re-validated: `.venv/bin/python -m pytest` passed on 2026-08-04 with 218 tests, `.venv/bin/python -m ruff check .` passed, `logics-manager lint` and `audit` passed. Shipped as v1.8.0 and verified in production.
- 2026-08-04, post-release, operator decision (v1.8.1): the parent link navigates in the current tab instead of opening a new one. `target="_blank"` and `rel="noopener noreferrer"` are dropped together, since both `noopener` and `noreferrer` only guard a spawned window; leaving for the parent site is now a departure the Back button undoes. `req_020` AC3, `item_099` AC3, and the `prod_024` decision were revised to match, and the test was renamed to `::test_the_parent_link_navigates_in_place_and_announces_its_destination`, asserting the absence of `target` and `rel`. Re-validated: `.venv/bin/python -m pytest` passed on 2026-08-04 with 218 tests, `.venv/bin/python -m ruff check .` passed, `logics-manager lint` and `audit` passed.

# Validation
- (no validation recorded yet)
- .venv/bin/python -m pytest tests/test_workspace_deliverables.py passed on 2026-08-04: 43 tests. .venv/bin/python -m pytest passed on 2026-08-04: 217 tests. .venv/bin/python -m ruff check . passed on 2026-08-04: All checks passed. .venv/bin/python -m hatchling build -t wheel -t sdist passed on 2026-08-04: claimlens/static/paulmondou-emblem.png present in both artifacts. logics-manager lint passed on 2026-08-04: OK. logics-manager audit passed on 2026-08-04: OK with one unrelated existing warning on prod_016.
- Finish workflow executed on 2026-08-04.
- Linked backlog/request close verification passed.

# Report
- Not started.
- Finished on 2026-08-04.
- Linked backlog item(s): `item_099_remplacer_l_avatar_de_navigation_par_l_embleme_paul_mondou`
- Related request(s): `req_020_remplacer_l_avatar_de_compte_par_le_lien_paul_mondou`

# AI Context
- Summary: Livrer le lien parent Paul Mondou dans la navigation ClaimLens
- Keywords: scaffolded-task, request-chain-scaffold, orchestration
- Use when: Coordinating implementation of a scaffolded request chain.
- Skip when: Working on one isolated sibling slice.

# Links
- Request: `req_020_remplacer_l_avatar_de_compte_par_le_lien_paul_mondou`
- Product brief(s): `prod_024_navigation_claimlens_reliee_au_site_parent`
- Architecture decision(s): (none yet)
