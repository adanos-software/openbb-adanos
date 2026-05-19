# App Spec: Adanos Market Sentiment

## Goal

Provide an OpenBB Workspace app backend for Adanos Market Sentiment API data without replacing the existing OpenBB provider extension.

## Data

- Source API: https://api.adanos.org/docs/
- Platforms: Reddit, News, X/Twitter, Polymarket.
- API key: provided per user through the OpenBB listing card or Data Connector credentials.
- Credential delivery: OpenBB sends the user's key as the `X-API-Key` header. Backend env vars `ADANOS_API_KEY` / `OPENBB_ADANOS_API_KEY` remain only as a local/private deployment fallback.

## Widgets

- `adanos_market_sentiment`: metric snapshot for a selected source and lookback.
- `adanos_trending`: table of trending sentiment rows with clickable symbols.
- `adanos_stock_sentiment`: table for one selected symbol.
- `adanos_compare`: table comparing up to 10 symbols.

## Layout

- Overview tab: market metrics, selected-symbol row, trending table.
- Compare tab: multi-symbol comparison table.
- Groups:
  - `Group 1`: `symbol`
  - `Group 2`: `source`
  - `Group 3`: `days`
