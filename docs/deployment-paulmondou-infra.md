# ClaimLens deployment in paulmondou-infra

ClaimLens should run as its own Docker Compose service behind Caddy.

## paulmondou-infra changes

Add to `.env`:

```bash
CLAIMLENS_DOMAIN=claimlens.paulmondou.fr
CLAIMLENS_APP_DIR=../ClaimLens
CLAIMLENS_KEY_ENCRYPTION_SECRET=<openssl rand -hex 32>
CLAIMLENS_SECURE_COOKIES=true
CLAIMLENS_REGISTRATION_ENABLED=false
CLAIMLENS_ALLOW_SERVER_API_KEY_FALLBACK=false
```

Add to `docker-compose.yml`:

```yaml
  claimlens:
    build:
      context: ${CLAIMLENS_APP_DIR:-../ClaimLens}
      dockerfile: Dockerfile
    restart: unless-stopped
    environment:
      CLAIMLENS_DB: /data/claimlens.sqlite3
      CLAIMLENS_OUTPUTS: /data/outputs
      CLAIMLENS_TRANSCRIPTS: /data/outputs/transcripts
      CLAIMLENS_BRIEFS: /data/outputs/briefs
      CLAIMLENS_HOST: 0.0.0.0
      CLAIMLENS_PORT: 8765
      CLAIMLENS_PUBLIC_BASE_URL: https://${CLAIMLENS_DOMAIN}
      CLAIMLENS_KEY_ENCRYPTION_SECRET: ${CLAIMLENS_KEY_ENCRYPTION_SECRET:?set it}
      CLAIMLENS_SECURE_COOKIES: ${CLAIMLENS_SECURE_COOKIES:-true}
      CLAIMLENS_REGISTRATION_ENABLED: ${CLAIMLENS_REGISTRATION_ENABLED:-false}
      CLAIMLENS_ALLOW_SERVER_API_KEY_FALLBACK: ${CLAIMLENS_ALLOW_SERVER_API_KEY_FALLBACK:-false}
    volumes:
      - claimlens-data:/data
    expose:
      - "8765"
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8765/health', timeout=3)"]
      interval: 30s
      timeout: 3s
      start_period: 10s
      retries: 3
```

Add to `Caddyfile`:

```caddyfile
{$CLAIMLENS_DOMAIN} {
	encode zstd gzip
	import security_headers
	reverse_proxy claimlens:8765
}
```

Add the volume:

```yaml
volumes:
  claimlens-data:
```

Deploy from `/home/paul/dev/paulmondou-infra` with:

```bash
DEPLOY_SSH=deploy@paulmondou.fr \
DEPLOY_SSH_KEY=/home/paul/dev/Kapsule/cle_hetzner \
DEPLOY_INFRA_SYNC_MODE=archive \
DEPLOY_APP_REPOS="ClaimLens:../ClaimLens:ClaimLens" \
./deploy.sh
```

## Security notes

- Keep `CLAIMLENS_KEY_ENCRYPTION_SECRET` outside Git and outside SQLite.
- Back up both the `claimlens-data` volume and the encryption secret. Losing the secret makes saved
  user API keys unrecoverable.
- Use Caddy HTTPS only. Do not publish the ClaimLens container port directly.
- Keep `CLAIMLENS_ALLOW_SERVER_API_KEY_FALLBACK=false` for BYO-key deployments.
- PubMed and Semantic Scholar can run without keys; saved user keys only improve quotas.

## VPS transcript fallback

If YouTube blocks the VPS IP, users can paste transcript text in the process page. The pasted text
is stored as `user_paste` and then follows the normal cleanup, analysis, brief, and verification
pipeline.
