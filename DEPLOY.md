# Deployment Guide

This guide is for taking Guni from local development to a production-style Railway deployment with healthier defaults for customer use.

## Current deployment shape

Guni is a FastAPI application served through Gunicorn/Uvicorn.

Important runtime behavior:

- the API serves static dashboard pages from `dashboard/`
- runtime state should live in a writable data directory
- the app exposes `/health` for healthchecks
- every GitHub push can redeploy Railway automatically

## Recommended production environment variables

Set these in Railway:

| Variable | Recommended value |
|---|---|
| `PORT` | Railway-provided |
| `GUNI_DATA_DIR` | `/data/guni` when a Railway Volume is mounted at `/data`; otherwise leave unset for ephemeral logs/state |
| `GUNI_MONGO_URI` | MongoDB connection string |
| `GUNI_MONGO_DB_NAME` | `guni` or your preferred database name |
| `GUNI_RATE_LIMIT` | `60` or your preferred limit |
| `GUNI_APP_BASE_URL` | Your Railway public URL, e.g. `https://your-service.up.railway.app` |
| `GUNI_CORS_ORIGINS` | Comma-separated allowed browser origins for cross-origin API calls |
| `GUNI_TRUSTED_HOSTS` | `your-service.up.railway.app,healthcheck.railway.app` (add your custom domain too, if used) |
| `GUNI_API_KEYS` | Comma-separated production keys if using protected mode |
| `GUNI_SESSION_SECRET` | Long random secret |
| `GUNI_LLM_API_KEY` | Optional default API key for hosted LLM reasoning |
| `GUNI_LLM_PROVIDER` | Optional default provider: `anthropic`, `openai`, `gemini`, or `openai_compatible` |
| `GUNI_LLM_MODEL` | Optional default model name |
| `GUNI_LLM_BASE_URL` | Optional default base URL for OpenAI-compatible providers |
| `GUNI_LLM_TIMEOUT_SECONDS` | LLM connection and response-read timeout in seconds (default: `60`) |
| `GUNI_LLM_CA_BUNDLE` | Optional path to a CA bundle for private/self-signed LLM endpoints |
| `GUNI_LLM_TLS_VERIFY` | Keep `true` in production; set `false` only for local self-signed testing |
| `GUNI_WORKER_TIMEOUT_SECONDS` | Gunicorn request-worker timeout in seconds (default: `90`) |
| `ANTHROPIC_API_KEY` | Legacy fallback for Anthropic |
| `RAZORPAY_KEY_ID` | Required for hosted checkout creation |
| `RAZORPAY_KEY_SECRET` | Required for hosted checkout creation |
| `RAZORPAY_WEBHOOK_SECRET` | Required for webhook verification |
| `BREVO_API_KEY` | Required for transactional email delivery |
| `GUNI_EMAIL_FROM` | Verified sender for transactional emails |

Optional overrides:

- `GUNI_DB_PATH`
- `GUNI_LOG_PATH`
- `GUNI_KEYS_PATH`
- `GUNI_WAITLIST_PATH`
- `GUNI_EVENT_LOG_PATH`

## Railway checklist

1. Push the repo to GitHub.
2. Create a Railway project from the repo and deploy the service. Railway will use the included `Dockerfile` and `railway.toml` automatically.
3. Generate the public Railway domain, then set `GUNI_APP_BASE_URL` and `GUNI_TRUSTED_HOSTS` using that hostname. `healthcheck.railway.app` must stay in `GUNI_TRUSTED_HOSTS` so Railway can reach `/health` during deploys.
4. Provision a MongoDB service or use MongoDB Atlas, then set `GUNI_MONGO_URI` to its connection string. This is required for accounts, API keys, scans, billing, and other persistent application features.
5. Set a long, random `GUNI_SESSION_SECRET`; keep `GUNI_ALLOW_OPEN_MODE=false` and `GUNI_ALLOW_PUBLIC_DEMO=false` in production.
6. Optionally attach a Railway Volume at `/data` and set `GUNI_DATA_DIR=/data/guni` for durable event logs and waitlist data.
7. Add the LLM, email, and Razorpay variables only for the integrations you intend to enable.
8. Verify `/health`, `/dashboard`, and `/enterprise` after deploy.

The included Railway health check is `GET /health`; it starts the service with `python start_server.py`, which binds Gunicorn to Railway's injected `PORT`.

## Render checklist

Render's generated `*.onrender.com` hostname is automatically trusted. Set
`GUNI_APP_BASE_URL` to the HTTPS URL shown in the Render dashboard and add any
custom domain to `GUNI_TRUSTED_HOSTS` as well. Deploy again after changing
environment variables.

## Verify the deploy

```bash
curl https://YOUR_URL/health
curl https://YOUR_URL/waitlist/count
```

For Docker Compose users, the included healthcheck now uses Python's standard library instead of `curl`, so it works with the shipped slim image without extra packages.

Scan smoke test:

```bash
curl -X POST https://YOUR_URL/scan \
  -H "X-API-Key: guni_live_..." \
  -H "Content-Type: application/json" \
  -d "{\"html\":\"<html><body><h1>hello</h1></body></html>\",\"goal\":\"Read page\"}"
```

If you intentionally want unauthenticated demo scans, you must explicitly set `GUNI_ALLOW_OPEN_MODE=true`. Do not enable that in production.

## Recommended customer-facing setup

For pilots:

- use the hosted API
- keep open mode only for demos
- share the dashboard and enterprise page during sales

For production customers:

- require `X-API-Key`
- use a durable MongoDB deployment for application data
- store runtime logs on a persistent volume if you want filesystem durability
- rotate keys deliberately
- set a strong `GUNI_SESSION_SECRET`
- set `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, and `RAZORPAY_WEBHOOK_SECRET` if you want in-product checkout
- decide whether the customer uses managed API or self-hosted mode

## CI recommendation

GitHub Actions CI is included in `.github/workflows/ci.yml`.

Before treating a branch as deployable, make sure:

- CI passes
- `pytest -q test_api.py` passes locally
- `/health` returns `ok` after deploy
