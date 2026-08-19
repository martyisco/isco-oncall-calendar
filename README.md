# ISCO After-Hours On-Call Calendar

A view-only on-call dashboard designed for a **public code repository** without exposing the ISCO roster or on-call schedule. The website is protected at runtime by Cloudflare Access/Entra SSO.

## Architecture

```text
Public GitHub repository
  └─ static UI + Pages Function source only; no schedule data

Cloudflare Pages
  └─ serves site/ and functions/api/schedule.js

Cloudflare Workers KV (private data)
  └─ key: schedule
  └─ value: generated six-month schedule JSON

Cloudflare Access
  └─ protects the custom hostname, including /api/schedule

Hermes on-call automation
  └─ reads the private authoritative YAML, generates six months, writes KV
```

The application code cannot administer the roster. It only reads `GET /api/schedule`, which is a Pages Function backed by the `ONCALL_SCHEDULE` KV binding.

## What is safe to publish

The repository must contain **only** application code, tests using fictional names, and documentation. Do not commit:

- responder names, email addresses, telephone numbers, or Telegram identities
- `rotation.yaml`, `schedule.json`, or export files
- Cloudflare API tokens, account credentials, webhook URLs, or iTop data

> This repository's prior private commits included a schedule-data implementation. Before making the repository public, create a clean public repository from the present allowlisted tree or rewrite Git history. A file deleted from the current branch still exists in prior commits.

## Cloudflare setup

### 1. Create the KV namespace

In the Cloudflare dashboard, go to **Workers & Pages → KV** and create a namespace, for example `isco-oncall-schedule`.

### 2. Create the Pages project

Create a Pages project with **Connect to Git**, choose the repository, and use:

- Production branch: `main`
- Framework preset: `None`
- Build command: *(leave blank)*
- Build output directory: `site`

In the Pages project, add a **KV namespace binding**:

- Variable name: `ONCALL_SCHEDULE`
- KV namespace: `isco-oncall-schedule`

The included Pages Function exposes that binding only at `GET /api/schedule`.

### 3. Protect the production hostname

Attach a custom hostname such as `oncall.isco-pipe.com`. In Cloudflare Zero Trust create an **Access → Applications → Self-hosted** application for that hostname and allow only ISCO Entra users. The policy must cover `/*`, which also protects `/api/schedule`.

Do not circulate the Pages preview hostname as an operational URL. Validate its access behavior separately from the custom-domain Access application.

## Publishing private schedule data

The publisher runs only from the trusted Hermes environment, never GitHub Actions in this public repository. It reads the private authoritative state and writes one KV key named `schedule`.

Required environment variables are stored outside this repository:

- `CLOUDFLARE_ACCOUNT_ID`
- `CLOUDFLARE_KV_NAMESPACE_ID`
- `CLOUDFLARE_API_TOKEN` — scope it to **Workers KV Storage: Edit** for only the required account/namespace

Example after Cloudflare setup:

```bash
python3 scripts/publish_schedule.py \
  --source ~/.hermes/oncall/isco-after-hours.yaml \
  --months-ahead 6
```

This regenerates a schedule through the end of the month six months ahead and uploads it directly to KV. No schedule file is written into the Git working tree.

## Monthly horizon

The trusted on-call automation runs the same publisher at the beginning of every month. That maintains six months of visible future coverage without placing changing schedule data into source control. An authorized schedule change runs the publisher immediately after the authoritative on-call YAML is updated.

## Local verification

```bash
python3 -m pip install -r requirements.txt
python3 -m unittest discover -s tests -v
node --check site/app.js
node --check functions/api/schedule.js
```

The UI needs the Pages Function and KV binding for live data, so a basic local static HTTP server will show the expected "temporarily unavailable" state unless a local function/KV emulator is configured.
