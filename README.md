# ISCO After-Hours On-Call Calendar

A view-only on-call dashboard. It deploys **directly to Cloudflare Workers** with static assets—no GitHub/Cloudflare repository connection and no Pages project required.

## Architecture

```text
Public GitHub repository
  └─ application source only; no schedule data

Cloudflare Worker
  ├─ serves static assets from site/
  └─ serves GET /api/schedule from Workers KV

Cloudflare Workers KV (private data)
  └─ key: schedule
  └─ generated six-month schedule JSON

Cloudflare Access / Entra SSO
  └─ protects the custom hostname, including /api/schedule

Trusted Hermes on-call automation
  └─ reads private source state, generates six months, writes KV
```

The Worker routes `/api/schedule` to the private `ONCALL_SCHEDULE` KV binding. All other requests are served from the bundled `site/` static assets.

## Why not “Upload static files” alone?

A static-only upload can serve HTML/CSS/JS, but it cannot read Workers KV. Use a **Worker with static assets** so one deployment serves both the website and its protected schedule endpoint. This deployment still has no repository connection: Wrangler directly uploads the Worker and `site/` assets to Cloudflare.

## Cloudflare setup

### 1. KV namespace

Create a KV namespace in **Cloudflare Dashboard → Storage & databases → KV**. The required binding name is:

`ONCALL_SCHEDULE`

### 2. Prepare direct Worker deployment

Copy `wrangler.jsonc` to your trusted Hermes deployment checkout and replace only:

`REPLACE_WITH_YOUR_KV_NAMESPACE_ID`

with the KV namespace ID shown in Cloudflare. Namespace IDs are identifiers, not credentials; do not commit the edited deployment configuration if you prefer to keep account metadata out of the public repository.

### 3. Create a narrowly scoped API token

Create a Cloudflare API token with only:

- **Account → Workers Scripts → Edit**
- **Account → Workers KV Storage → Edit**

Do not paste it in Telegram or commit it. Store it on the Hermes host as `CLOUDFLARE_API_TOKEN`. Also configure `CLOUDFLARE_ACCOUNT_ID` and `CLOUDFLARE_KV_NAMESPACE_ID` only in the trusted Hermes environment.

### 4. Direct deploy

From the trusted deployment checkout:

```bash
npx wrangler@latest deploy
```

Wrangler uploads the Worker and `site/` assets directly. It does not clone, fork, or connect to GitHub.

### 5. Custom hostname and Access

Add a custom hostname such as `oncall.isco-pipe.com` to the Worker. In Cloudflare Zero Trust, create a **Self-hosted** Access application for that hostname. Allow only ISCO Entra identities and cover `/*` so `/api/schedule` is protected too.

## Publish private schedule data

The publisher runs only from trusted Hermes automation. It never writes schedule data into Git.

```bash
python3 scripts/publish_schedule.py \
  --source ~/.hermes/oncall/isco-after-hours.yaml \
  --months-ahead 6
```

It reads the authoritative private YAML, creates coverage through the end of the month six months ahead, and overwrites the KV key `schedule`.

Run it immediately after an authorized rotation change and monthly at the beginning of each month.

## Local verification

```bash
python3 -m pip install -r requirements.txt
python3 -m unittest discover -s tests -v
node --test tests/test_worker.mjs
node --check site/app.js
```

## Public-source boundary

Do not commit roster names, email addresses, phone numbers, Telegram identities, generated schedules, Cloudflare API tokens, private endpoint URLs, or private state exports. The repository deliberately contains only code, generic documentation, and fictional test data.
