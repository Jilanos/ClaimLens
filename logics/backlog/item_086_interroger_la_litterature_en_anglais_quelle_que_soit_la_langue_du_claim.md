## item_086_interroger_la_litterature_en_anglais_quelle_que_soit_la_langue_du_claim - Interroger la litterature en anglais quelle que soit la langue du claim
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Medium
> Theme: Multilingual evidence retrieval
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- Un claim énoncé en français est envoyé tel quel à PubMed et Semantic Scholar, qui indexent en anglais, et ne renvoie rien.
- L'absence de résultat se lit comme un silence de la science alors que la question n'a jamais été posée dans la bonne langue.

# Scope
- In:
  - Frontière LLM de traduction des claims vers l'anglais, par lot et bornée.
  - Texte de recherche anglais porté par la requête provider, distinct du claim affiché.
  - Jugement des sources sur le claim anglais, prose destinée au lecteur dans la langue du rapport.
  - Repli explicite et tracé lorsque la traduction est indisponible.
- Out:
  - Traduction du brief, des titres d'articles ou de l'interface.
  - Détection de langue côté transcription et changement du modèle d'analyse.

# Acceptance criteria
- AC1: Un claim français atteint les adaptateurs sous sa forme anglaise.
- AC2: Le brief affiche le claim tel qu'il a été énoncé, sans fuite de la traduction.
- AC3: Le grader et la synthèse reçoivent le claim anglais, puisqu'ils lisent des résumés anglais.
- AC4: La prose rendue au lecteur suit la langue du rapport.
- AC5: Une traduction en échec laisse la vérification aboutir et apparaît dans les résultats d'adaptateur.
- AC6: Une traduction incomplète ne décale jamais un claim sur le texte de recherche d'un autre.

# AC Traceability
- request-AC3 -> This backlog slice. Proof: `test_a_french_claim_is_searched_in_english` asserts the adapter receives the English wording.
- request-AC4 -> This backlog slice. Proof: `test_the_reader_still_sees_the_claim_as_it_was_said` asserts the brief keeps the original claim and leaks no translation.
- request-AC5 -> This backlog slice. Proof: `test_the_grader_and_the_synthesizer_judge_the_english_claim` and `test_prose_follows_the_report_language_while_judgement_stays_english`.
- request-AC6 -> This backlog slice. Proof: `test_a_failed_translation_searches_the_claim_as_written` keeps the run succeeded and records a `claim_translation` outcome.
- request-AC7 -> This backlog slice. Proof: translation, fallback and ordering coverage in `tests/test_verification.py`.
- request-AC1 -> This backlog slice. Evidence needed: L'en-tête de l'application affiche la marque retenue, combinant loupe, triangle de lecture et coche de revue, à la place de l'ancienne loupe.
- request-AC2 -> This backlog slice. Evidence needed: Chaque page sert une icône d'onglet inline reprenant exactement la même marque sur la tuile de marque, sans requête supplémentaire.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Delivery notes
- `OpenAIClaimTranslator` in `src/claimlens/evidence.py` renders every claim in English in one batched call before any provider is queried.
- `SourceQuery.search_text` carries the English wording to the adapters, while `SourceQuery.claim` stays the wording the viewer heard; the brief renders the latter.
- The grader and the synthesizer read English abstracts, so they judge the English claim, and both write their prose in the report language through `language_instruction`.
- A failed or short translation falls back to the original text per claim and is recorded as a `claim_translation` outcome, never as a failed verification.

# Links
- Product brief(s): `prod_019_marque_claimlens_et_recherche_scientifique_independante_de_la_langue`
- Architecture decision(s): (none yet)
- Request: `req_015_donner_a_claimlens_sa_marque_propre_et_une_recherche_scientifique_independante_de_la_langue`
- Primary task(s): `task_019_livrer_la_marque_claimlens_et_la_recherche_scientifique_multilingue`

# AI Context
- Summary: Interroger la litterature en anglais quelle que soit la langue du claim
- Keywords: scaffolded-backlog, interroger la litterature en anglais quelle que soit la langue du claim, implementation-ready
- Use when: Implementing the scaffolded slice for Interroger la litterature en anglais quelle que soit la langue du claim.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.

# Tasks
- `task_019_livrer_la_marque_claimlens_et_la_recherche_scientifique_multilingue`

# Notes
- Task `task_019_livrer_la_marque_claimlens_et_la_recherche_scientifique_multilingue` was finished via `logics-manager flow finish task` on 2026-08-03.
