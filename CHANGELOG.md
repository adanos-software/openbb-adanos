# Changelog

## 1.1.0 - 2026-03-16

- Added a full OpenBB core router surface under `obb.adanos.<platform>.*` for Reddit, News, X/Twitter, and Polymarket.
- Added support for all major Adanos stock endpoints: trending, sector trends, country trends, stock detail, search, compare, stats, health, and explain where supported.
- Fixed OpenBB credential registration so the provider now correctly uses `adanos_api_key`.
- Expanded provider-level models to carry platform-specific detail fields for news, X, and Polymarket.
- Added automated tests for the HTTP client, fetchers, and OpenBB router extension.
