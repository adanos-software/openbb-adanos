"""HTTP client utilities for the Adanos Market Sentiment API."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Sequence

import httpx

DEFAULT_BASE_URL = "https://api.adanos.org"
BASE_URL_ENV_VAR = "OPENBB_ADANOS_BASE_URL"
API_KEY_ENV_VARS = ("OPENBB_ADANOS_API_KEY", "ADANOS_API_KEY")


@dataclass(frozen=True)
class PlatformDefinition:
    """Static metadata for a supported Adanos platform."""

    name: str
    prefix: str
    supports_explain: bool = False
    supports_source_filter: bool = False


PLATFORMS = {
    "reddit": PlatformDefinition(
        name="reddit",
        prefix="/reddit/stocks/v1",
        supports_explain=True,
    ),
    "news": PlatformDefinition(
        name="news",
        prefix="/news/stocks/v1",
        supports_explain=True,
        supports_source_filter=True,
    ),
    "x": PlatformDefinition(
        name="x",
        prefix="/x/stocks/v1",
        supports_explain=True,
    ),
    "polymarket": PlatformDefinition(
        name="polymarket",
        prefix="/polymarket/stocks/v1",
    ),
}

PLATFORM_ALIASES = {
    "reddit": "reddit",
    "news": "news",
    "x": "x",
    "twitter": "x",
    "x/twitter": "x",
    "polymarket": "polymarket",
}

ASSET_TYPES = {"stock", "etf", "all"}


def _coerce_secret(value: Any) -> str | None:
    """Extract a plain string from raw credential values."""
    if value is None:
        return None
    if hasattr(value, "get_secret_value"):
        value = value.get_secret_value()
    value = str(value).strip()
    return value or None


def get_base_url(base_url: str | None = None) -> str:
    """Resolve the API base URL, allowing test and local overrides."""
    value = (base_url or os.getenv(BASE_URL_ENV_VAR) or DEFAULT_BASE_URL).strip()
    return value.rstrip("/")


def normalize_platform(platform: str) -> str:
    """Normalize platform aliases to canonical API platform names."""
    normalized = PLATFORM_ALIASES.get(str(platform or "").strip().lower())
    if normalized is None:
        choices = ", ".join(sorted(PLATFORMS))
        raise ValueError(f"Unknown platform '{platform}'. Choose from: {choices}.")
    return normalized


def get_platform_definition(platform: str) -> PlatformDefinition:
    """Return metadata for a supported platform."""
    return PLATFORMS[normalize_platform(platform)]


def normalize_asset_type(asset_type: str | None) -> str | None:
    """Validate asset-type filters."""
    if asset_type is None:
        return None
    normalized = str(asset_type).strip().lower()
    if normalized not in ASSET_TYPES:
        choices = ", ".join(sorted(ASSET_TYPES))
        raise ValueError(f"Unknown asset_type '{asset_type}'. Choose from: {choices}.")
    return normalized


def validate_days(days: int) -> int:
    """Validate shared day range used by the API."""
    if not 1 <= int(days) <= 90:
        raise ValueError("days must be between 1 and 90.")
    return int(days)


def validate_limit(limit: int) -> int:
    """Validate shared list size limits."""
    if not 1 <= int(limit) <= 100:
        raise ValueError("limit must be between 1 and 100.")
    return int(limit)


def validate_offset(offset: int) -> int:
    """Validate pagination offset."""
    if int(offset) < 0:
        raise ValueError("offset must be greater than or equal to 0.")
    return int(offset)


def normalize_symbols(
    symbols: Sequence[str] | str,
    *,
    max_items: int | None = None,
) -> list[str]:
    """Normalize and deduplicate ticker inputs."""
    if isinstance(symbols, str):
        raw_items = symbols.split(",")
    else:
        raw_items = list(symbols)

    normalized: list[str] = []
    seen: set[str] = set()

    for item in raw_items:
        symbol = str(item).strip().upper().replace("$", "")
        if not symbol or symbol in seen:
            continue
        seen.add(symbol)
        normalized.append(symbol)

    if not normalized:
        raise ValueError("At least one symbol is required.")

    if max_items is not None and len(normalized) > max_items:
        raise ValueError(f"At most {max_items} symbols are allowed.")

    return normalized


def resolve_api_key(
    *,
    credentials: dict[str, Any] | None = None,
    api_key: str | None = None,
    required: bool = True,
) -> str | None:
    """Resolve the API key from explicit values, OpenBB credentials, or env vars."""
    explicit = _coerce_secret(api_key)
    if explicit:
        return explicit

    if credentials:
        for key in ("adanos_api_key", "api_key", "adanos_adanos_api_key"):
            resolved = _coerce_secret(credentials.get(key))
            if resolved:
                return resolved

    for env_var in API_KEY_ENV_VARS:
        resolved = _coerce_secret(os.getenv(env_var))
        if resolved:
            return resolved

    if required:
        raise ValueError(
            "Missing Adanos API key. Set obb.user.credentials.adanos_api_key "
            f"or one of: {', '.join(API_KEY_ENV_VARS)}."
        )

    return None


class _PlatformNamespace:
    """Convenience wrapper for one Adanos platform namespace."""

    def __init__(self, client: "AdanosClient", platform: str):
        self._client = client
        self._platform = get_platform_definition(platform)

    @property
    def name(self) -> str:
        """Canonical platform name."""
        return self._platform.name

    def trending(
        self,
        *,
        days: int = 1,
        limit: int = 20,
        offset: int = 0,
        asset_type: str | None = None,
        source: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get trending stocks for a platform."""
        params = {
            "days": validate_days(days),
            "limit": validate_limit(limit),
            "offset": validate_offset(offset),
        }
        normalized_type = normalize_asset_type(asset_type)
        if normalized_type is not None:
            params["type"] = normalized_type
        if source is not None:
            if not self._platform.supports_source_filter:
                raise ValueError(
                    f"Platform '{self._platform.name}' does not support a source filter."
                )
            params["source"] = str(source).strip()
        return self._client.get_json(f"{self._platform.prefix}/trending", params=params)

    def trending_sectors(
        self,
        *,
        days: int = 1,
        limit: int = 20,
        offset: int = 0,
        source: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get sector aggregations for a platform."""
        params = {
            "days": validate_days(days),
            "limit": validate_limit(limit),
            "offset": validate_offset(offset),
        }
        if source is not None:
            if not self._platform.supports_source_filter:
                raise ValueError(
                    f"Platform '{self._platform.name}' does not support a source filter."
                )
            params["source"] = str(source).strip()
        return self._client.get_json(
            f"{self._platform.prefix}/trending/sectors",
            params=params,
        )

    def trending_countries(
        self,
        *,
        days: int = 1,
        limit: int = 20,
        offset: int = 0,
        source: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get country aggregations for a platform."""
        params = {
            "days": validate_days(days),
            "limit": validate_limit(limit),
            "offset": validate_offset(offset),
        }
        if source is not None:
            if not self._platform.supports_source_filter:
                raise ValueError(
                    f"Platform '{self._platform.name}' does not support a source filter."
                )
            params["source"] = str(source).strip()
        return self._client.get_json(
            f"{self._platform.prefix}/trending/countries",
            params=params,
        )

    def stock(self, symbol: str, *, days: int = 7) -> dict[str, Any]:
        """Get detailed stock sentiment or market-activity data."""
        ticker = normalize_symbols([symbol], max_items=1)[0]
        params = {"days": validate_days(days)}
        return self._client.get_json(f"{self._platform.prefix}/stock/{ticker}", params=params)

    def explain(self, symbol: str) -> dict[str, Any]:
        """Get an AI explanation for why a stock is trending."""
        if not self._platform.supports_explain:
            raise ValueError(
                f"Platform '{self._platform.name}' does not provide /explain."
            )
        ticker = normalize_symbols([symbol], max_items=1)[0]
        return self._client.get_json(f"{self._platform.prefix}/stock/{ticker}/explain")

    def search(self, query: str, *, days: int = 7, limit: int = 20) -> dict[str, Any]:
        """Search stocks within a platform universe."""
        cleaned = str(query).strip()
        if not cleaned:
            raise ValueError("query must not be empty.")
        return self._client.get_json(
            f"{self._platform.prefix}/search",
            params={"q": cleaned, "days": validate_days(days), "limit": validate_limit(limit)},
        )

    def compare(
        self,
        symbols: Sequence[str] | str,
        *,
        days: int = 7,
    ) -> dict[str, Any]:
        """Compare up to 10 symbols side by side."""
        tickers = normalize_symbols(symbols, max_items=10)
        params = {
            "tickers": ",".join(tickers),
            "days": validate_days(days),
        }
        return self._client.get_json(f"{self._platform.prefix}/compare", params=params)

    def market_sentiment(self, *, days: int = 1) -> dict[str, Any]:
        """Get the service-level market sentiment snapshot for a platform."""
        params = {"days": validate_days(days)}
        return self._client.get_json(f"{self._platform.prefix}/market-sentiment", params=params)

    def stats(self) -> dict[str, Any]:
        """Get dataset coverage stats for a platform."""
        return self._client.get_json(f"{self._platform.prefix}/stats")

    def health(self) -> dict[str, Any]:
        """Get the public health payload for a platform."""
        return self._client.get_json(f"{self._platform.prefix}/health")


class AdanosClient:
    """Ergonomic synchronous client for the Adanos API."""

    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str | None = None,
        timeout: float = 30.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        headers: dict[str, str] = {
            "Accept": "application/json",
            "User-Agent": "openbb-adanos/1.0",
        }
        if resolved := resolve_api_key(api_key=api_key, required=False):
            headers["X-API-Key"] = resolved

        self._client = httpx.Client(
            base_url=get_base_url(base_url),
            timeout=timeout,
            headers=headers,
            transport=transport,
        )
        self.reddit = _PlatformNamespace(self, "reddit")
        self.news = _PlatformNamespace(self, "news")
        self.x = _PlatformNamespace(self, "x")
        self.polymarket = _PlatformNamespace(self, "polymarket")

    def get_json(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """Execute a GET request and decode the JSON payload."""
        filtered_params = {
            key: value for key, value in (params or {}).items() if value is not None
        }
        response = self._client.get(path, params=filtered_params)
        response.raise_for_status()
        return response.json()

    def platform(self, platform: str) -> _PlatformNamespace:
        """Access a platform namespace dynamically."""
        return getattr(self, normalize_platform(platform))

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()

    def __enter__(self) -> "AdanosClient":
        return self

    def __exit__(self, *_args: Any) -> None:
        self.close()


def get_stock_sentiment(
    symbol: str,
    source: str,
    api_key: str,
    days: int = 7,
) -> dict[str, Any]:
    """Fetch sentiment for a single stock."""
    with AdanosClient(api_key=api_key) as client:
        return client.platform(source).stock(symbol, days=days)


def get_trending(
    source: str,
    api_key: str,
    days: int = 1,
    limit: int = 20,
    offset: int = 0,
    asset_type: str | None = None,
    news_source: str | None = None,
) -> list[dict[str, Any]]:
    """Fetch trending stocks for a supported platform."""
    with AdanosClient(api_key=api_key) as client:
        return client.platform(source).trending(
            days=days,
            limit=limit,
            offset=offset,
            asset_type=asset_type,
            source=news_source,
        )


def get_compare(
    symbols: Sequence[str] | str,
    source: str,
    api_key: str,
    days: int = 7,
) -> dict[str, Any]:
    """Fetch comparison data for multiple stocks."""
    with AdanosClient(api_key=api_key) as client:
        return client.platform(source).compare(symbols, days=days)


def get_market_sentiment(
    *,
    source: str,
    api_key: str,
    days: int = 1,
) -> dict[str, Any]:
    """Fetch the service-level market sentiment snapshot for one platform."""
    with AdanosClient(api_key=api_key) as client:
        return client.platform(source).market_sentiment(days=days)


def get_trending_dimensions(
    *,
    source: str,
    dimension: str,
    api_key: str,
    days: int = 1,
    limit: int = 20,
    offset: int = 0,
    news_source: str | None = None,
) -> list[dict[str, Any]]:
    """Fetch sector or country trend aggregations."""
    with AdanosClient(api_key=api_key) as client:
        namespace = client.platform(source)
        if dimension == "sectors":
            return namespace.trending_sectors(
                days=days,
                limit=limit,
                offset=offset,
                source=news_source,
            )
        if dimension == "countries":
            return namespace.trending_countries(
                days=days,
                limit=limit,
                offset=offset,
                source=news_source,
            )
        raise ValueError("dimension must be either 'sectors' or 'countries'.")


def search_stocks(
    query: str,
    *,
    source: str,
    api_key: str,
    days: int = 7,
    limit: int = 20,
) -> dict[str, Any]:
    """Search stocks within one platform namespace."""
    with AdanosClient(api_key=api_key) as client:
        return client.platform(source).search(query, days=days, limit=limit)


def get_stats(
    *,
    source: str,
    api_key: str,
) -> dict[str, Any]:
    """Fetch dataset stats for a platform."""
    with AdanosClient(api_key=api_key) as client:
        return client.platform(source).stats()


def get_health(
    *,
    source: str,
    api_key: str | None = None,
) -> dict[str, Any]:
    """Fetch the public health status for a platform."""
    with AdanosClient(api_key=api_key) as client:
        return client.platform(source).health()


def get_stock_explanation(
    symbol: str,
    *,
    source: str,
    api_key: str,
) -> dict[str, Any]:
    """Fetch the AI explanation for a stock."""
    with AdanosClient(api_key=api_key) as client:
        return client.platform(source).explain(symbol)


__all__ = [
    "API_KEY_ENV_VARS",
    "AdanosClient",
    "DEFAULT_BASE_URL",
    "PLATFORMS",
    "PlatformDefinition",
    "get_base_url",
    "get_compare",
    "get_health",
    "get_market_sentiment",
    "get_platform_definition",
    "get_stats",
    "get_stock_explanation",
    "get_stock_sentiment",
    "get_trending",
    "get_trending_dimensions",
    "normalize_asset_type",
    "normalize_platform",
    "normalize_symbols",
    "resolve_api_key",
    "search_stocks",
]
