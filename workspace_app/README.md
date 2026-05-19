# Adanos Market Sentiment OpenBB Workspace App

FastAPI backend for OpenBB Workspace widgets powered by the Adanos Market Sentiment API.

## What It Adds

- Market-level sentiment metrics for Reddit, News, X/Twitter, and Polymarket.
- Trending sentiment table with click-to-select symbol behavior.
- Selected-symbol sentiment table.
- Multi-symbol comparison table.

## Run Locally

From the repository root:

```bash
pip install -e .
pip install -r workspace_app/requirements.txt
uvicorn workspace_app.main:app --reload --host 0.0.0.0 --port 7779
```

Then add `http://localhost:7779` in OpenBB Workspace:

```text
Settings -> Data Connectors -> Add data connector
```

## API Key

The app metadata endpoints (`/widgets.json` and `/apps.json`) are public so OpenBB can discover the app. For marketplace deployments, users enter their own Adanos API key through the OpenBB listing card, and OpenBB forwards it to this backend as `X-API-Key`.

Local/private Workspace setup:

```text
Header: X-API-Key
Value: sk_live_...
```

Local backend-only fallback:

```bash
export ADANOS_API_KEY=sk_live_...
```

API docs: https://api.adanos.org/docs/

## Endpoints

- `GET /widgets.json`
- `GET /apps.json`
- `GET /market_sentiment?source=reddit&days=7`
- `GET /trending?source=reddit&days=7&limit=20&asset_type=stock`
- `GET /stock_sentiment?symbol=AAPL&source=reddit&days=7`
- `GET /compare?symbols=AAPL,MSFT,NVDA&source=reddit&days=7`
