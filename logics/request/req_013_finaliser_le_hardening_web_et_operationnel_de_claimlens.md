## req_013_finaliser_le_hardening_web_et_operationnel_de_claimlens - Finaliser le hardening web et operationnel de ClaimLens
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Complexity: High
> Theme: Production security and reliability follow-up
> Reminder: Update status/understanding/confidence and linked backlog/task references when you edit this doc.

# Needs
- Rendre la limitation anonyme fiable derriere Caddy sans faire confiance a une IP fournie par le client.
- Prouver les garanties du serveur HTTP par des tests d'integration multi-client.
- Borner et rendre observable l'execution des jobs web.
- Permettre la rotation verifiable des cles de chiffrement des API keys et renforcer la chaine CI/CD.

# Context
- L'audit de reanalyse constate que web.py utilise X-Real-IP pour une seconde limite anonyme, tandis que le Caddyfile documente ne reecrit pas explicitement cet en-tete.
- Les tests actuels couvrent les services et rendus, mais ne demarrent pas le ThreadingHTTPServer ni deux clients HTTP independants.
- Les secrets nouvellement ecrits utilisent AES-GCM v2 mais aucun mecanisme de key_id, de rotation ou de migration v1 vers v2 n'est livre.
- Les jobs restent executes par un ThreadPoolExecutor en memoire; apres redemarrage ils sont interrompus et la file n'a ni limite explicite ni metriques operationnelles.
- Le chantier ne modifie pas les regles de polarite, les libelles ou la promesse produit du mode source-verified.

# Acceptance criteria
- AC1: Le deploiement Caddy transmet une identite client fiable, un client ne peut pas contourner la limite anonyme en forgeant X-Real-IP, et l'application refuse ou ignore les headers forwarded hors proxy de confiance.
- AC2: Une suite HTTP demarre le serveur reel et couvre cookies, CSRF, corps trop volumineux, redirections, isolation de deux clients, rapports, limites de debit et comportement derriere proxy.
- AC3: La file de jobs est bornee, sa saturation est restituee clairement, les transitions et echecs sont observables, et le redemarrage conserve une experience retryable coherente.
- AC4: Les API keys stockees disposent d'un format versionne avec key_id, d'une rotation transactionnelle testee et d'un chemin de migration v1 vers AES-GCM v2.
- AC5: La CI valide aussi l'image Docker; les actions, artefacts SBOM/provenance et le deploiement d'image sont rendus tracables et reproductibles.

# Definition of Ready (DoR)
- [x] Problem statement is explicit and user impact is clear.
- [x] Scope boundaries (in/out) are explicit.
- [x] Acceptance criteria are testable.
- [x] Dependencies and known risks are listed.

# Companion docs
- Product brief(s): `prod_017_hardening_de_production_claimlens_suivi`
- Architecture decision(s): (none yet)

# References
- AUDIT_TECHNIQUE.md
- src/claimlens/web.py
- src/claimlens/secrets.py
- .github/workflows/ci.yml
- docs/deployment-paulmondou-infra.md

# AI Context
- Summary: Finaliser le hardening web et operationnel de ClaimLens
- Keywords: request-chain-scaffold, finaliser le hardening web et operationnel de claimlens, development-ready
- Use when: You need to implement or review the scaffolded workflow for Finaliser le hardening web et operationnel de ClaimLens.
- Skip when: The change is unrelated to this scaffolded request chain.

# Backlog
- `item_077_fiabiliser_l_identite_client_derriere_le_reverse_proxy_et_tester_le_serveur_http`
- `item_078_borner_et_observer_la_file_de_jobs_web`
- `item_079_rendre_les_secrets_applicatifs_rotatifs_et_migrables`
- `item_080_rendre_la_chaine_ci_cd_conteneurisee_tracable`
