# openbb-adanos

[![PyPI version](https://img.shields.io/pypi/v/openbb-adanos.svg)](https://pypi.org/project/openbb-adanos/)

Adanos market-sentiment integration for the [OpenBB Platform](https://github.com/OpenBB-finance/OpenBB).

The package now exposes two layers:

- Standard OpenBB provider commands for quick cross-platform sentiment lookups.
- A full `obb.adanos.<platform>.*` router surface for all Adanos stock endpoints.
- An OpenBB Workspace app backend in `workspace_app/` for dashboards and widgets.

Links:

- Source: https://github.com/adanos-software/openbb-adanos
- API docs: https://api.adanos.org/docs
- Homepage: https://adanos.org

## Installation

```bash
pip install openbb-adanos
```

## Setup

Get an API key at [api.adanos.org](https://api.adanos.org), then configure OpenBB:

```python
from openbb import obb

obb.user.credentials.adanos_api_key = "sk_live_..."
```

You can also use `OPENBB_ADANOS_API_KEY`.

## OpenBB Workspace App

The `workspace_app/` directory contains a FastAPI backend for OpenBB Workspace Data Connectors. It exposes `/widgets.json`, `/apps.json`, and Adanos sentiment endpoints for a ready-made dashboard.

Run it locally from the repository root:

```bash
pip install -e .
pip install -r workspace_app/requirements.txt
uvicorn workspace_app.main:app --reload --host 0.0.0.0 --port 7779
```

Then add `http://localhost:7779` in OpenBB Workspace Data Connectors. For live data, add the custom connector header `X-API-Key: sk_live_...` or set `ADANOS_API_KEY` on the backend.

## Quick Start

### Standard OpenBB provider flow

```python
from openbb import obb

# Single symbol, detailed sentiment
obb.equity.sentiment(symbol="AAPL", provider="adanos")

# Cross-platform support
obb.equity.sentiment(symbol="TSLA", source="x", provider="adanos")
obb.equity.sentiment(symbol="NVDA", source="news", provider="adanos")
obb.equity.sentiment(symbol="SPY", source="polymarket", provider="adanos")

# Trending list
obb.equity.sentiment.trending(provider="adanos")
obb.equity.sentiment.trending(source="news", days=3, limit=50, provider="adanos")

# Compact comparison
obb.equity.sentiment.compare(symbols="AAPL,MSFT,NVDA", provider="adanos")
```

### Full Adanos endpoint surface inside OpenBB

```python
from openbb import obb

# Reddit
obb.adanos.reddit.trending(days=1, limit=25)
obb.adanos.reddit.stock(symbol="TSLA", days=7)
obb.adanos.reddit.market_sentiment(days=7)
obb.adanos.reddit.explain(symbol="TSLA")
obb.adanos.reddit.search(query="tesla")
obb.adanos.reddit.compare(symbols=["TSLA", "NVDA", "AMD"])
obb.adanos.reddit.stats()
obb.adanos.reddit.health()

# News
obb.adanos.news.trending(days=3, source="reuters")
obb.adanos.news.trending_sectors(days=7, source="bloomberg")
obb.adanos.news.trending_countries(days=7)
obb.adanos.news.stock(symbol="AAPL", days=14)
obb.adanos.news.market_sentiment(days=7)
obb.adanos.news.explain(symbol="AAPL")

# X / Twitter
obb.adanos.x.trending(days=1, asset_type="stock")
obb.adanos.x.stock(symbol="TSLA", days=7)
obb.adanos.x.market_sentiment(days=7)
obb.adanos.x.explain(symbol="TSLA")
obb.adanos.x.search(query="nvidia")

# Polymarket
obb.adanos.polymarket.trending(days=7)
obb.adanos.polymarket.stock(symbol="NVDA", days=14)
obb.adanos.polymarket.market_sentiment(days=7)
obb.adanos.polymarket.compare(symbols="NVDA,TSLA,AMD")
```

## Supported Endpoints

### Provider commands

- `obb.equity.sentiment(..., provider="adanos")`
- `obb.equity.sentiment.trending(..., provider="adanos")`
- `obb.equity.sentiment.compare(..., provider="adanos")`

### Router commands

- `obb.adanos.reddit.{trending,trending_sectors,trending_countries,stock,market_sentiment,explain,search,compare,stats,health}`
- `obb.adanos.news.{trending,trending_sectors,trending_countries,stock,market_sentiment,explain,search,compare,stats,health}`
- `obb.adanos.x.{trending,trending_sectors,trending_countries,stock,market_sentiment,explain,search,compare,stats,health}`
- `obb.adanos.polymarket.{trending,trending_sectors,trending_countries,stock,market_sentiment,search,compare,stats,health}`

## Notes

- Provider-level `source` supports `reddit`, `news`, `x`, and `polymarket`.
- Trending defaults to `days=1`, matching the API behavior.
- Full stock detail remains platform-specific through `obb.adanos.*.stock(...)`, so users get fields like `top_tweets`, `source_distribution`, or `top_mentions` instead of a flattened lowest-common-denominator response.
