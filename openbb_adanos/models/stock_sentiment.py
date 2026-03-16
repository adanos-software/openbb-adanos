"""Single-stock sentiment model and fetcher."""

from typing import Any, Optional

from openbb_core.provider.abstract.data import Data
from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.abstract.query_params import QueryParams
from pydantic import Field

from openbb_adanos.utils.client import get_stock_sentiment, resolve_api_key


class AdanosStockSentimentQueryParams(QueryParams):
    """Query parameters for Adanos stock sentiment."""

    symbol: str = Field(description="Stock ticker symbol (e.g. AAPL, TSLA).")
    source: str = Field(
        default="reddit",
        description="Platform: 'reddit', 'news', 'x', or 'polymarket'.",
    )
    days: int = Field(
        default=7,
        description="Lookback period in days (1-30 free, 1-90 paid).",
        ge=1,
        le=90,
    )


class AdanosStockSentimentData(Data):
    """Stock sentiment data from the Adanos API."""

    symbol: str = Field(description="Stock ticker symbol.")
    company_name: Optional[str] = Field(default=None, description="Company name.")
    found: Optional[bool] = Field(default=None, description="Whether the symbol had platform data.")
    buzz_score: Optional[float] = Field(default=None, description="Buzz score (0-100).")
    sentiment_score: Optional[float] = Field(
        default=None, description="Sentiment score (-1.0 bearish to +1.0 bullish)."
    )
    total_mentions: Optional[int] = Field(default=None, description="Total mentions in period.")
    positive_count: Optional[int] = Field(default=None, description="Positive mentions or markets.")
    negative_count: Optional[int] = Field(default=None, description="Negative mentions or markets.")
    neutral_count: Optional[int] = Field(default=None, description="Neutral mentions or markets.")
    unique_posts: Optional[int] = Field(default=None, description="Unique posts/tweets.")
    unique_tweets: Optional[int] = Field(default=None, description="Unique tweets on X.")
    source_count: Optional[int] = Field(default=None, description="News source count.")
    trade_count: Optional[int] = Field(default=None, description="Trade count on Polymarket.")
    market_count: Optional[int] = Field(default=None, description="Active Polymarket market count.")
    unique_traders: Optional[int] = Field(default=None, description="Best-effort Polymarket trader count.")
    total_liquidity: Optional[float] = Field(
        default=None,
        description="Windowed Polymarket liquidity signal.",
    )
    trend: Optional[str] = Field(default=None, description="Trend direction: rising, falling, stable.")
    bullish_pct: Optional[float] = Field(default=None, description="Percentage of bullish mentions.")
    bearish_pct: Optional[float] = Field(default=None, description="Percentage of bearish mentions.")
    total_upvotes: Optional[int] = Field(default=None, description="Total upvotes/likes.")
    subreddit_count: Optional[int] = Field(
        default=None, description="Number of subreddits (Reddit only)."
    )
    is_validated: Optional[bool] = Field(
        default=None,
        description="Whether X activity is validated by Reddit activity.",
    )
    period_days: Optional[int] = Field(default=None, description="Analysis period in days.")
    source: Optional[str] = Field(
        default=None,
        description="Platform source (reddit, news, x, polymarket).",
    )
    daily_trend: Optional[list[dict[str, Any]]] = Field(default=None, description="Daily trend data.")
    top_mentions: Optional[list[dict[str, Any]]] = Field(default=None, description="Top mentions or markets.")
    top_subreddits: Optional[list[dict[str, Any]]] = Field(
        default=None,
        description="Top subreddits for Reddit stocks.",
    )
    top_tweets: Optional[list[dict[str, Any]]] = Field(default=None, description="Top tweets for X stocks.")
    source_distribution: Optional[dict[str, int]] = Field(
        default=None,
        description="News source distribution by mention count.",
    )


class AdanosStockSentimentFetcher(
    Fetcher[AdanosStockSentimentQueryParams, list[AdanosStockSentimentData]]
):
    """Fetcher for Adanos single-stock sentiment data."""

    @staticmethod
    def transform_query(params: dict[str, Any]) -> AdanosStockSentimentQueryParams:
        """Transform query parameters."""
        return AdanosStockSentimentQueryParams(**params)

    @staticmethod
    def extract_data(
        query: AdanosStockSentimentQueryParams,
        credentials: Optional[dict[str, str]],
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Fetch raw data from Adanos API."""
        api_key = resolve_api_key(credentials=credentials)
        return get_stock_sentiment(
            symbol=query.symbol,
            source=query.source,
            api_key=api_key,
            days=query.days,
        )

    @staticmethod
    def transform_data(
        query: AdanosStockSentimentQueryParams,
        data: dict[str, Any],
        **kwargs: Any,
    ) -> list[AdanosStockSentimentData]:
        """Transform raw API response to data model."""
        if not data or not data.get("found", True):
            return []

        return [
            AdanosStockSentimentData(
                symbol=data.get("ticker", query.symbol),
                company_name=data.get("company_name"),
                found=data.get("found"),
                buzz_score=data.get("buzz_score"),
                sentiment_score=data.get("sentiment_score"),
                total_mentions=(
                    data.get("total_mentions")
                    if data.get("total_mentions") is not None
                    else data.get("trade_count")
                ),
                positive_count=data.get("positive_count"),
                negative_count=data.get("negative_count"),
                neutral_count=data.get("neutral_count"),
                unique_posts=data.get("unique_posts") or data.get("unique_tweets"),
                unique_tweets=data.get("unique_tweets"),
                source_count=data.get("source_count"),
                trade_count=data.get("trade_count"),
                market_count=data.get("market_count"),
                unique_traders=data.get("unique_traders"),
                total_liquidity=data.get("total_liquidity"),
                trend=data.get("trend"),
                bullish_pct=data.get("bullish_pct"),
                bearish_pct=data.get("bearish_pct"),
                total_upvotes=data.get("total_upvotes"),
                subreddit_count=data.get("subreddit_count"),
                is_validated=data.get("is_validated"),
                period_days=data.get("period_days"),
                source=query.source,
                daily_trend=data.get("daily_trend"),
                top_mentions=data.get("top_mentions"),
                top_subreddits=data.get("top_subreddits"),
                top_tweets=data.get("top_tweets"),
                source_distribution=data.get("source_distribution"),
            )
        ]
