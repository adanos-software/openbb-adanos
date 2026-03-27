# Changelog

## 1.3.0 - 2026-03-27

- Added `market_sentiment(days=...)` to the OpenBB Adanos router and HTTP client for Reddit, News, X/Twitter, and Polymarket.
- Renamed package metadata and docs from stock-sentiment wording to Adanos Market Sentiment branding.

## 1.2.2 - 2026-03-25

- Fixed OpenBB core router code generation so `obb.adanos.<platform>.*` routes build and run correctly in a clean local OpenBB install.

## 1.2.1 - 2026-03-19

- Fixed OpenBB search payload normalization so `period_days` remains available in router `extra` metadata.

## 1.2.0 - 2026-03-19

- Updated compare models to the enriched `/compare` contract, including `trend`, `trend_history`, and platform-specific activity fields.
- Updated search support to the current API `summary` contract with `days` and `limit`.
- Updated stock detail handling to prefer canonical `mentions` while keeping compatibility with the legacy `total_mentions` alias.

## 1.1.0 - 2026-03-16

- Added a full OpenBB core router surface under `obb.adanos.<platform>.*` for Reddit, News, X/Twitter, and Polymarket.
- Added support for all major Adanos stock endpoints: trending, sector trends, country trends, stock detail, search, compare, stats, health, and explain where supported.
- Fixed OpenBB credential registration so the provider now correctly uses `adanos_api_key`.
- Expanded provider-level models to carry platform-specific detail fields for news, X, and Polymarket.
- Added automated tests for the HTTP client, fetchers, and OpenBB router extension.
