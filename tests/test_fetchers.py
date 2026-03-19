"""Tests for Adanos OpenBB provider fetchers."""

from unittest.mock import patch

from openbb_adanos import adanos_provider
from openbb_adanos.models.compare import AdanosCompareFetcher
from openbb_adanos.models.stock_sentiment import AdanosStockSentimentFetcher
from openbb_adanos.models.trending import AdanosTrendingFetcher

MOCK_STOCK_RESPONSE = {
    "ticker": "AAPL",
    "company_name": "Apple Inc.",
    "found": True,
    "buzz_score": 72.5,
    "sentiment_score": 0.34,
    "mentions": 412,
    "total_mentions": 412,
    "positive_count": 180,
    "negative_count": 54,
    "neutral_count": 178,
    "unique_posts": 89,
    "trend": "rising",
    "bullish_pct": 61.2,
    "bearish_pct": 18.4,
    "total_upvotes": 15320,
    "subreddit_count": 8,
    "period_days": 7,
    "daily_trend": [{"date": "2026-03-15", "mentions": 23, "sentiment_score": 0.4, "sentiment": 0.4}],
}

MOCK_X_STOCK_RESPONSE = {
    "ticker": "TSLA",
    "company_name": "Tesla, Inc.",
    "found": True,
    "buzz_score": 68.1,
    "sentiment_score": 0.12,
    "mentions": 125,
    "total_mentions": 125,
    "positive_count": 51,
    "negative_count": 22,
    "neutral_count": 52,
    "unique_tweets": 42,
    "total_upvotes": 8300,
    "is_validated": True,
    "top_tweets": [{"author": "trader", "likes": 300}],
}

MOCK_POLYMARKET_STOCK_RESPONSE = {
    "ticker": "NVDA",
    "company_name": "NVIDIA Corporation",
    "found": True,
    "buzz_score": 63.4,
    "trade_count": 91,
    "market_count": 8,
    "unique_traders": 44,
    "sentiment_score": 0.18,
}

MOCK_TRENDING_RESPONSE = [
    {
        "ticker": "NVDA",
        "company_name": "NVIDIA Corporation",
        "buzz_score": 88.1,
        "sentiment_score": 0.52,
        "mentions": 1024,
        "trend": "rising",
        "bullish_pct": 71.0,
        "bearish_pct": 12.3,
        "total_upvotes": 45200,
        "subreddit_count": 12,
        "unique_posts": 203,
        "trend_history": [21.0, 35.5, 88.1],
    },
    {
        "ticker": "TSLA",
        "company_name": "Tesla, Inc.",
        "buzz_score": 65.3,
        "sentiment_score": -0.12,
        "trade_count": 780,
        "market_count": 19,
        "unique_traders": 156,
        "trend": "falling",
        "bullish_pct": 38.5,
        "bearish_pct": 42.1,
        "total_liquidity": 22100.5,
    },
]

MOCK_COMPARE_RESPONSE = {
    "period_days": 7,
    "stocks": [
        {
            "ticker": "AAPL",
            "company_name": "Apple Inc.",
            "buzz_score": 72.5,
            "trend": "rising",
            "sentiment_score": 0.34,
            "sentiment": 0.34,
            "mentions": 412,
            "unique_posts": 89,
            "subreddit_count": 8,
            "bullish_pct": 61.2,
            "bearish_pct": 18.4,
            "total_upvotes": 15320,
            "trend_history": [41.0, 55.2, 72.5],
        },
        {
            "ticker": "NVDA",
            "company_name": "NVIDIA Corporation",
            "buzz_score": 58.2,
            "trend": "stable",
            "sentiment_score": 0.21,
            "sentiment": 0.21,
            "trade_count": 287,
            "market_count": 12,
            "unique_traders": 98,
            "bullish_pct": 54.0,
            "bearish_pct": 22.0,
            "total_liquidity": 9800.5,
            "trend_history": [44.1, 49.2, 58.2],
        },
    ],
}


class TestProviderConfiguration:
    def test_provider_uses_single_prefixed_credential(self):
        assert adanos_provider.credentials == ["adanos_api_key"]


class TestStockSentimentFetcher:
    def test_transform_query_defaults(self):
        query = AdanosStockSentimentFetcher.transform_query({"symbol": "AAPL"})
        assert query.symbol == "AAPL"
        assert query.source == "reddit"
        assert query.days == 7

    def test_transform_query_supports_news(self):
        query = AdanosStockSentimentFetcher.transform_query(
            {"symbol": "AAPL", "source": "news", "days": 14}
        )
        assert query.source == "news"
        assert query.days == 14

    @patch("openbb_adanos.models.stock_sentiment.get_stock_sentiment")
    def test_extract_data_uses_resolved_api_key(self, mock_get):
        mock_get.return_value = MOCK_STOCK_RESPONSE
        query = AdanosStockSentimentFetcher.transform_query({"symbol": "AAPL"})
        data = AdanosStockSentimentFetcher.extract_data(
            query,
            credentials={"api_key": "sk_live_test"},
        )
        mock_get.assert_called_once_with(
            symbol="AAPL",
            source="reddit",
            api_key="sk_live_test",
            days=7,
        )
        assert data["ticker"] == "AAPL"

    def test_transform_data_reddit_fields(self):
        query = AdanosStockSentimentFetcher.transform_query({"symbol": "AAPL"})
        result = AdanosStockSentimentFetcher.transform_data(query, MOCK_STOCK_RESPONSE)

        assert len(result) == 1
        item = result[0]
        assert item.symbol == "AAPL"
        assert item.buzz_score == 72.5
        assert item.mentions == 412
        assert item.total_mentions == 412
        assert item.positive_count == 180
        assert item.daily_trend == [{"date": "2026-03-15", "mentions": 23, "sentiment_score": 0.4, "sentiment": 0.4}]

    def test_transform_data_x_specific_fields(self):
        query = AdanosStockSentimentFetcher.transform_query({"symbol": "TSLA", "source": "x"})
        result = AdanosStockSentimentFetcher.transform_data(query, MOCK_X_STOCK_RESPONSE)

        item = result[0]
        assert item.mentions == 125
        assert item.unique_posts == 42
        assert item.unique_tweets == 42
        assert item.is_validated is True
        assert item.top_tweets == [{"author": "trader", "likes": 300}]

    def test_transform_data_polymarket_backfills_total_mentions_from_trade_count(self):
        query = AdanosStockSentimentFetcher.transform_query(
            {"symbol": "NVDA", "source": "polymarket"}
        )
        result = AdanosStockSentimentFetcher.transform_data(
            query,
            MOCK_POLYMARKET_STOCK_RESPONSE,
        )

        item = result[0]
        assert item.mentions == 91
        assert item.total_mentions == 91
        assert item.trade_count == 91

    def test_transform_data_not_found(self):
        query = AdanosStockSentimentFetcher.transform_query({"symbol": "FAKE"})
        assert AdanosStockSentimentFetcher.transform_data(query, {"found": False}) == []


class TestTrendingFetcher:
    def test_transform_query_defaults(self):
        query = AdanosTrendingFetcher.transform_query({})
        assert query.source == "reddit"
        assert query.days == 1
        assert query.limit == 20
        assert query.offset == 0
        assert query.asset_type is None

    def test_transform_query_custom(self):
        query = AdanosTrendingFetcher.transform_query(
            {
                "source": "polymarket",
                "days": 3,
                "limit": 50,
                "offset": 10,
                "asset_type": "etf",
            }
        )
        assert query.source == "polymarket"
        assert query.limit == 50
        assert query.offset == 10
        assert query.asset_type == "etf"

    @patch("openbb_adanos.models.trending.get_trending")
    def test_extract_data(self, mock_get):
        mock_get.return_value = MOCK_TRENDING_RESPONSE
        query = AdanosTrendingFetcher.transform_query({"source": "reddit", "limit": 10})
        data = AdanosTrendingFetcher.extract_data(
            query,
            credentials={"adanos_api_key": "sk_live_test"},
        )
        mock_get.assert_called_once_with(
            source="reddit",
            api_key="sk_live_test",
            days=1,
            limit=10,
            offset=0,
            asset_type=None,
        )
        assert len(data) == 2

    def test_transform_data_maps_social_and_polymarket_fields(self):
        query = AdanosTrendingFetcher.transform_query({"source": "polymarket"})
        result = AdanosTrendingFetcher.transform_data(query, MOCK_TRENDING_RESPONSE)

        assert len(result) == 2
        assert result[0].symbol == "NVDA"
        assert result[0].trend_history == [21.0, 35.5, 88.1]
        assert result[1].mentions == 780
        assert result[1].trade_count == 780
        assert result[1].market_count == 19
        assert result[1].total_liquidity == 22100.5


class TestCompareFetcher:
    def test_transform_query(self):
        query = AdanosCompareFetcher.transform_query({"symbols": "AAPL,MSFT,TSLA", "days": 14})
        assert query.symbols == "AAPL,MSFT,TSLA"
        assert query.days == 14
        assert query.source == "reddit"

    @patch("openbb_adanos.models.compare.get_compare")
    def test_extract_data(self, mock_get):
        mock_get.return_value = MOCK_COMPARE_RESPONSE
        query = AdanosCompareFetcher.transform_query({"symbols": "AAPL,MSFT"})
        data = AdanosCompareFetcher.extract_data(
            query,
            credentials={"adanos_api_key": "sk_live_test"},
        )
        mock_get.assert_called_once_with(
            symbols=["AAPL", "MSFT"],
            source="reddit",
            api_key="sk_live_test",
            days=7,
        )
        assert "stocks" in data

    def test_transform_data_maps_sentiment_and_polymarket_fields(self):
        query = AdanosCompareFetcher.transform_query({"symbols": "AAPL,NVDA"})
        result = AdanosCompareFetcher.transform_data(query, MOCK_COMPARE_RESPONSE)

        assert len(result) == 2
        assert result[0].symbol == "AAPL"
        assert result[0].trend == "rising"
        assert result[0].sentiment_score == 0.34
        assert result[0].unique_posts == 89
        assert result[0].trend_history == [41.0, 55.2, 72.5]
        assert result[1].mentions == 287
        assert result[1].total_upvotes is None
        assert result[1].trade_count == 287
        assert result[1].market_count == 12
        assert result[1].total_liquidity == 9800.5
        assert result[1].trend_history == [44.1, 49.2, 58.2]
