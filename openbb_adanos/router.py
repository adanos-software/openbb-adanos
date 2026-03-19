"""OpenBB router extension exposing the full Adanos platform surface."""

from __future__ import annotations

from typing import Any, Literal

from openbb_core.app.model.obbject import OBBject
from openbb_core.app.model.user_settings import UserSettings
from openbb_core.app.router import Router

from openbb_adanos.utils.client import AdanosClient, resolve_api_key

router = Router(
    prefix="",
    description=(
        "Full Adanos API integration for Reddit, News, X/Twitter, and Polymarket "
        "stock sentiment data."
    ),
)


def _user_settings() -> UserSettings:
    """Resolve the active OpenBB user settings context."""
    current = getattr(OBBject, "_user_settings", None)
    if isinstance(current, UserSettings):
        return current

    return UserSettings()


def _build_client(
    *,
    require_api_key: bool = True,
) -> AdanosClient:
    """Create an Adanos client from OpenBB credentials or environment variables."""
    settings = _user_settings()
    credentials = (
        settings.credentials.model_dump()
        if getattr(settings, "credentials", None) is not None
        else None
    )
    api_key = resolve_api_key(credentials=credentials, required=require_api_key)
    return AdanosClient(api_key=api_key)


def _to_obbject(platform: str, route: str, payload: Any) -> OBBject:
    """Normalize payloads into an OBBject optimized for downstream use."""
    results = payload
    extra: dict[str, Any] = {"platform": platform, "route": route}

    if isinstance(payload, dict):
        if route == "search":
            results = payload.get("results", [])
            extra.update(
                {
                    "query": payload.get("query"),
                    "count": payload.get("count"),
                }
            )
        elif route == "compare":
            results = payload.get("stocks", [])
            extra["period_days"] = payload.get("period_days")

    return OBBject(results=results, provider="adanos", extra=extra)


def _create_platform_router(
    *,
    platform: str,
    description: str,
    supports_explain: bool = False,
    supports_source_filter: bool = False,
) -> Router:
    """Create a nested router for one Adanos platform."""
    platform_router = Router(prefix="", description=description)

    if supports_source_filter:

        @platform_router.command(
            no_validate=True,
            path="/trending",
            operation_id=f"{platform}_trending",
        )
        def trending(
            days: int = 1,
            limit: int = 20,
            offset: int = 0,
            asset_type: Literal["stock", "etf", "all"] | None = None,
            source: str | None = None,
        ) -> OBBject:
            """Get trending stocks for one Adanos platform."""
            with _build_client(require_api_key=True) as client:
                payload = client.platform(platform).trending(
                    days=days,
                    limit=limit,
                    offset=offset,
                    asset_type=asset_type,
                    source=source,
                )
            return _to_obbject(platform, "trending", payload)

        @platform_router.command(
            no_validate=True,
            path="/trending_sectors",
            operation_id=f"{platform}_trending_sectors",
        )
        def trending_sectors(
            days: int = 1,
            limit: int = 20,
            offset: int = 0,
            source: str | None = None,
        ) -> OBBject:
            """Get sector-level trend aggregations for one Adanos platform."""
            with _build_client(require_api_key=True) as client:
                payload = client.platform(platform).trending_sectors(
                    days=days,
                    limit=limit,
                    offset=offset,
                    source=source,
                )
            return _to_obbject(platform, "trending_sectors", payload)

        @platform_router.command(
            no_validate=True,
            path="/trending_countries",
            operation_id=f"{platform}_trending_countries",
        )
        def trending_countries(
            days: int = 1,
            limit: int = 20,
            offset: int = 0,
            source: str | None = None,
        ) -> OBBject:
            """Get country-level trend aggregations for one Adanos platform."""
            with _build_client(require_api_key=True) as client:
                payload = client.platform(platform).trending_countries(
                    days=days,
                    limit=limit,
                    offset=offset,
                    source=source,
                )
            return _to_obbject(platform, "trending_countries", payload)

    else:

        @platform_router.command(
            no_validate=True,
            path="/trending",
            operation_id=f"{platform}_trending",
        )
        def trending(
            days: int = 1,
            limit: int = 20,
            offset: int = 0,
            asset_type: Literal["stock", "etf", "all"] | None = None,
        ) -> OBBject:
            """Get trending stocks for one Adanos platform."""
            with _build_client(require_api_key=True) as client:
                payload = client.platform(platform).trending(
                    days=days,
                    limit=limit,
                    offset=offset,
                    asset_type=asset_type,
                )
            return _to_obbject(platform, "trending", payload)

        @platform_router.command(
            no_validate=True,
            path="/trending_sectors",
            operation_id=f"{platform}_trending_sectors",
        )
        def trending_sectors(
            days: int = 1,
            limit: int = 20,
            offset: int = 0,
        ) -> OBBject:
            """Get sector-level trend aggregations for one Adanos platform."""
            with _build_client(require_api_key=True) as client:
                payload = client.platform(platform).trending_sectors(
                    days=days,
                    limit=limit,
                    offset=offset,
                )
            return _to_obbject(platform, "trending_sectors", payload)

        @platform_router.command(
            no_validate=True,
            path="/trending_countries",
            operation_id=f"{platform}_trending_countries",
        )
        def trending_countries(
            days: int = 1,
            limit: int = 20,
            offset: int = 0,
        ) -> OBBject:
            """Get country-level trend aggregations for one Adanos platform."""
            with _build_client(require_api_key=True) as client:
                payload = client.platform(platform).trending_countries(
                    days=days,
                    limit=limit,
                    offset=offset,
                )
            return _to_obbject(platform, "trending_countries", payload)

    @platform_router.command(
        no_validate=True,
        path="/stock",
        operation_id=f"{platform}_stock",
    )
    def stock(
        symbol: str,
        days: int = 7,
    ) -> OBBject:
        """Get the detailed stock view for one symbol."""
        with _build_client(require_api_key=True) as client:
            payload = client.platform(platform).stock(symbol, days=days)
        return _to_obbject(platform, "stock", payload)

    if supports_explain:

        @platform_router.command(
            no_validate=True,
            path="/explain",
            operation_id=f"{platform}_explain",
        )
        def explain(
            symbol: str,
        ) -> OBBject:
            """Get the AI explanation for why a symbol is trending."""
            with _build_client(require_api_key=True) as client:
                payload = client.platform(platform).explain(symbol)
            return _to_obbject(platform, "explain", payload)

    @platform_router.command(
        no_validate=True,
        path="/search",
        operation_id=f"{platform}_search",
    )
    def search(
        query: str,
        days: int = 7,
        limit: int = 20,
    ) -> OBBject:
        """Search symbols by ticker, company name, or alias."""
        with _build_client(require_api_key=True) as client:
            payload = client.platform(platform).search(query, days=days, limit=limit)
        return _to_obbject(platform, "search", payload)

    @platform_router.command(
        no_validate=True,
        path="/compare",
        operation_id=f"{platform}_compare",
    )
    def compare(
        symbols: str | list[str],
        days: int = 7,
    ) -> OBBject:
        """Compare up to 10 symbols side by side."""
        with _build_client(require_api_key=True) as client:
            payload = client.platform(platform).compare(symbols, days=days)
        return _to_obbject(platform, "compare", payload)

    @platform_router.command(
        no_validate=True,
        path="/stats",
        operation_id=f"{platform}_stats",
    )
    def stats(
    ) -> OBBject:
        """Get dataset coverage stats for a platform."""
        with _build_client(require_api_key=True) as client:
            payload = client.platform(platform).stats()
        return _to_obbject(platform, "stats", payload)

    @platform_router.command(
        no_validate=True,
        path="/health",
        operation_id=f"{platform}_health",
    )
    def health(
    ) -> OBBject:
        """Get the public health status for a platform."""
        with _build_client(require_api_key=False) as client:
            payload = client.platform(platform).health()
        return _to_obbject(platform, "health", payload)

    return platform_router


router.include_router(
    _create_platform_router(
        platform="reddit",
        description="Reddit stock sentiment endpoints.",
        supports_explain=True,
    ),
    prefix="/reddit",
)
router.include_router(
    _create_platform_router(
        platform="news",
        description="News stock sentiment endpoints.",
        supports_explain=True,
        supports_source_filter=True,
    ),
    prefix="/news",
)
router.include_router(
    _create_platform_router(
        platform="x",
        description="X/Twitter stock sentiment endpoints.",
    ),
    prefix="/x",
)
router.include_router(
    _create_platform_router(
        platform="polymarket",
        description="Polymarket stock activity endpoints.",
    ),
    prefix="/polymarket",
)

__all__ = ["router"]
