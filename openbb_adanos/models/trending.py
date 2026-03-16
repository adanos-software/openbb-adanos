"""Trending stocks by sentiment model and fetcher."""

from typing import Any, Optional

from openbb_core.provider.abstract.data import Data
from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.abstract.query_params import QueryParams
from pydantic import Field

from openbb_adanos.utils.client import get_trending, resolve_api_key


class AdanosTrendingQueryParams(QueryParams):
    """Query parameters for Adanos trending stocks."""

    source: str = Field(
        default="reddit",
        description="Platform: 'reddit', 'news', 'x', or 'polymarket'.",
    )
    days: int = Field(
        default=1,
        description="Lookback period in days (1-30 free, 1-90 paid).",
        ge=1,
        le=90,
    )
    limit: int = Field(
        default=20,
        description="Maximum number of results (1-100).",
        ge=1,
        le=100,
    )
    asset_type: Optional[str] = Field(
        default=None,
        description="Filter by asset type: 'stock', 'etf', or 'all'.",
    )
    offset: int = Field(
        default=0,
        description="Number of items to skip for pagination.",
        ge=0,
    )


class AdanosTrendingData(Data):
    """Trending stock sentiment data from the Adanos API."""

    symbol: str = Field(description="Stock ticker symbol.")
    company_name: Optional[str] = Field(default=None, description="Company name.")
    buzz_score: Optional[float] = Field(default=None, description="Buzz score (0-100).")
    sentiment_score: Optional[float] = Field(
        default=None, description="Sentiment score (-1.0 bearish to +1.0 bullish)."
    )
    mentions: Optional[int] = Field(default=None, description="Total mentions in period.")
    trend: Optional[str] = Field(default=None, description="Trend direction: rising, falling, stable.")
    bullish_pct: Optional[float] = Field(default=None, description="Percentage of bullish mentions.")
    bearish_pct: Optional[float] = Field(default=None, description="Percentage of bearish mentions.")
    total_upvotes: Optional[int] = Field(default=None, description="Total upvotes/likes.")
    subreddit_count: Optional[int] = Field(
        default=None, description="Number of subreddits (Reddit only)."
    )
    unique_posts: Optional[int] = Field(default=None, description="Unique posts/tweets.")
    unique_tweets: Optional[int] = Field(default=None, description="Unique tweets on X.")
    source_count: Optional[int] = Field(default=None, description="News source count.")
    unique_authors: Optional[int] = Field(default=None, description="Unique authors on X.")
    trade_count: Optional[int] = Field(default=None, description="Trade count on Polymarket.")
    market_count: Optional[int] = Field(default=None, description="Active market count on Polymarket.")
    unique_traders: Optional[int] = Field(default=None, description="Best-effort trader count.")
    total_liquidity: Optional[float] = Field(default=None, description="Windowed Polymarket liquidity.")
    is_validated: Optional[bool] = Field(
        default=None,
        description="Whether X activity is also validated by Reddit activity.",
    )
    trend_history: Optional[list[float]] = Field(default=None, description="Recent buzz history.")
    source: Optional[str] = Field(
        default=None,
        description="Platform source (reddit, news, x, polymarket).",
    )


class AdanosTrendingFetcher(
    Fetcher[AdanosTrendingQueryParams, list[AdanosTrendingData]]
):
    """Fetcher for Adanos trending sentiment data."""

    @staticmethod
    def transform_query(params: dict[str, Any]) -> AdanosTrendingQueryParams:
        """Transform query parameters."""
        return AdanosTrendingQueryParams(**params)

    @staticmethod
    def extract_data(
        query: AdanosTrendingQueryParams,
        credentials: Optional[dict[str, str]],
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """Fetch raw trending data from Adanos API."""
        api_key = resolve_api_key(credentials=credentials)
        return get_trending(
            source=query.source,
            api_key=api_key,
            days=query.days,
            limit=query.limit,
            offset=query.offset,
            asset_type=query.asset_type,
        )

    @staticmethod
    def transform_data(
        query: AdanosTrendingQueryParams,
        data: list[dict[str, Any]],
        **kwargs: Any,
    ) -> list[AdanosTrendingData]:
        """Transform raw API response to data model."""
        results = []
        for item in data:
            results.append(
                AdanosTrendingData(
                    symbol=item.get("ticker", ""),
                    company_name=item.get("company_name"),
                    buzz_score=item.get("buzz_score"),
                    sentiment_score=item.get("sentiment_score"),
                    mentions=(
                        item.get("mentions")
                        if item.get("mentions") is not None
                        else item.get("trade_count")
                    ),
                    trend=item.get("trend"),
                    bullish_pct=item.get("bullish_pct"),
                    bearish_pct=item.get("bearish_pct"),
                    total_upvotes=item.get("total_upvotes"),
                    subreddit_count=item.get("subreddit_count"),
                    unique_posts=item.get("unique_posts") or item.get("unique_tweets"),
                    unique_tweets=item.get("unique_tweets"),
                    source_count=item.get("source_count"),
                    unique_authors=item.get("unique_authors"),
                    trade_count=item.get("trade_count"),
                    market_count=item.get("market_count"),
                    unique_traders=item.get("unique_traders"),
                    total_liquidity=item.get("total_liquidity"),
                    is_validated=item.get("is_validated"),
                    trend_history=item.get("trend_history"),
                    source=query.source,
                )
            )
        return results
