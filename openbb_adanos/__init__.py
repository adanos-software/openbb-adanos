"""Adanos Market Sentiment provider and router extensions for OpenBB."""

from openbb_core.provider.abstract.provider import Provider

from openbb_adanos.models.compare import AdanosCompareFetcher
from openbb_adanos.models.stock_sentiment import AdanosStockSentimentFetcher
from openbb_adanos.models.trending import AdanosTrendingFetcher
from openbb_adanos.utils.client import AdanosClient

__version__ = "1.4.1"

adanos_provider = Provider(
    name="adanos",
    description="Market sentiment data from Reddit, News, X/Twitter, and Polymarket. "
    "Provides buzz scores, service-level market sentiment snapshots, trending stocks, "
    "sector/country aggregates, search, platform health, and cross-platform comparison. "
    "Get a free API key at https://api.adanos.org",
    website="https://api.adanos.org",
    credentials=["api_key"],
    instructions=(
        "Set your key with `obb.user.credentials.adanos_api_key = 'sk_live_...'` "
        "or export OPENBB_ADANOS_API_KEY."
    ),
    fetcher_dict={
        "StockSentiment": AdanosStockSentimentFetcher,
        "SentimentTrending": AdanosTrendingFetcher,
        "SentimentCompare": AdanosCompareFetcher,
    },
)

__all__ = ["AdanosClient", "__version__", "adanos_provider"]
