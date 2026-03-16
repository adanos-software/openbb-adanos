"""Compare multiple stocks by sentiment model and fetcher."""

from typing import Any, Optional

from openbb_core.provider.abstract.data import Data
from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.abstract.query_params import QueryParams
from pydantic import Field

from openbb_adanos.utils.client import get_compare, resolve_api_key


class AdanosCompareQueryParams(QueryParams):
    """Query parameters for Adanos stock comparison."""

    symbols: str = Field(
        description="Comma-separated ticker symbols to compare (max 10). E.g. 'AAPL,TSLA,MSFT'."
    )
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


class AdanosCompareData(Data):
    """Comparison sentiment data from the Adanos API."""

    symbol: str = Field(description="Stock ticker symbol.")
    company_name: Optional[str] = Field(default=None, description="Company name.")
    buzz_score: Optional[float] = Field(default=None, description="Buzz score (0-100).")
    sentiment_score: Optional[float] = Field(
        default=None, description="Sentiment score (-1.0 bearish to +1.0 bullish)."
    )
    mentions: Optional[int] = Field(default=None, description="Total mentions in period.")
    total_upvotes: Optional[int] = Field(default=None, description="Total upvotes/likes/trades.")
    source_count: Optional[int] = Field(default=None, description="News source count.")
    trade_count: Optional[int] = Field(default=None, description="Polymarket trade count.")
    market_count: Optional[int] = Field(default=None, description="Polymarket market count.")
    unique_traders: Optional[int] = Field(default=None, description="Best-effort trader count.")
    total_liquidity: Optional[float] = Field(default=None, description="Windowed Polymarket liquidity.")
    source: Optional[str] = Field(
        default=None,
        description="Platform source (reddit, news, x, polymarket).",
    )


class AdanosCompareFetcher(
    Fetcher[AdanosCompareQueryParams, list[AdanosCompareData]]
):
    """Fetcher for Adanos compare sentiment data."""

    @staticmethod
    def transform_query(params: dict[str, Any]) -> AdanosCompareQueryParams:
        """Transform query parameters."""
        return AdanosCompareQueryParams(**params)

    @staticmethod
    def extract_data(
        query: AdanosCompareQueryParams,
        credentials: Optional[dict[str, str]],
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Fetch raw comparison data from Adanos API."""
        api_key = resolve_api_key(credentials=credentials)
        symbols = [s.strip() for s in query.symbols.split(",")]
        return get_compare(
            symbols=symbols,
            source=query.source,
            api_key=api_key,
            days=query.days,
        )

    @staticmethod
    def transform_data(
        query: AdanosCompareQueryParams,
        data: dict[str, Any],
        **kwargs: Any,
    ) -> list[AdanosCompareData]:
        """Transform raw API response to data model."""
        results = []
        for item in data.get("stocks", []):
            results.append(
                AdanosCompareData(
                    symbol=item.get("ticker", ""),
                    company_name=item.get("company_name"),
                    buzz_score=item.get("buzz_score"),
                    sentiment_score=item.get("sentiment_score", item.get("sentiment")),
                    mentions=(
                        item.get("mentions")
                        if item.get("mentions") is not None
                        else item.get("trade_count")
                    ),
                    total_upvotes=item.get("total_upvotes"),
                    source_count=item.get("source_count"),
                    trade_count=item.get("trade_count"),
                    market_count=item.get("market_count"),
                    unique_traders=item.get("unique_traders"),
                    total_liquidity=item.get("total_liquidity"),
                    source=query.source,
                )
            )
        return results
