"""Tests for the Adanos HTTP client utilities."""

from __future__ import annotations

import httpx
import pytest

from openbb_adanos.utils.client import (
    AdanosClient,
    get_trending_dimensions,
    normalize_platform,
    normalize_symbols,
    resolve_api_key,
)


def _transport(recorder, payload):
    def handler(request: httpx.Request) -> httpx.Response:
        recorder.append(request)
        return httpx.Response(200, json=payload)

    return httpx.MockTransport(handler)


def test_reddit_trending_builds_expected_request():
    requests = []
    with AdanosClient(
        api_key="sk_live_test",
        transport=_transport(requests, [{"ticker": "AAPL"}]),
    ) as client:
        payload = client.reddit.trending(days=3, limit=15, offset=5, asset_type="etf")

    assert payload == [{"ticker": "AAPL"}]
    request = requests[0]
    assert request.url.path == "/reddit/stocks/v1/trending"
    assert dict(request.url.params) == {
        "days": "3",
        "limit": "15",
        "offset": "5",
        "type": "etf",
    }
    assert request.headers["X-API-Key"] == "sk_live_test"


def test_news_trending_supports_source_filter():
    requests = []
    with AdanosClient(
        api_key="sk_live_test",
        transport=_transport(requests, [{"ticker": "MSFT"}]),
    ) as client:
        payload = client.news.trending(days=2, source="reuters")

    assert payload == [{"ticker": "MSFT"}]
    assert requests[0].url.path == "/news/stocks/v1/trending"
    assert dict(requests[0].url.params)["source"] == "reuters"


def test_explain_validation_rejects_unsupported_platform():
    with AdanosClient(
        api_key="sk_live_test",
        transport=httpx.MockTransport(lambda request: httpx.Response(200)),
    ) as client:
        with pytest.raises(ValueError, match="does not provide /explain"):
            client.x.explain("TSLA")


def test_compare_normalizes_symbol_lists():
    requests = []
    with AdanosClient(
        api_key="sk_live_test",
        transport=_transport(requests, {"stocks": []}),
    ) as client:
        payload = client.polymarket.compare(["tsla", "$nvda", "tsla"], days=4)

    assert payload == {"stocks": []}
    assert requests[0].url.path == "/polymarket/stocks/v1/compare"
    assert dict(requests[0].url.params) == {"tickers": "TSLA,NVDA", "days": "4"}


def test_search_includes_days_and_limit():
    requests = []
    with AdanosClient(
        api_key="sk_live_test",
        transport=_transport(requests, {"query": "tesla", "count": 0, "period_days": 14, "results": []}),
    ) as client:
        payload = client.reddit.search("tesla", days=14, limit=5)

    assert payload["period_days"] == 14
    assert requests[0].url.path == "/reddit/stocks/v1/search"
    assert dict(requests[0].url.params) == {"q": "tesla", "days": "14", "limit": "5"}


def test_market_sentiment_uses_service_endpoint():
    requests = []
    payload = {"buzz_score": 57.4, "drivers": [{"ticker": "SPY"}]}

    with AdanosClient(
        api_key="sk_live_test",
        transport=_transport(requests, payload),
    ) as client:
        result = client.reddit.market_sentiment(days=7)

    assert result["buzz_score"] == 57.4
    assert requests[0].url.path == "/reddit/stocks/v1/market-sentiment"
    assert dict(requests[0].url.params) == {"days": "7"}


def test_get_health_works_without_api_key():
    requests = []
    payload = {"status": "healthy"}

    with AdanosClient(transport=_transport(requests, payload)) as client:
        assert client.reddit.health() == payload

    assert "X-API-Key" not in requests[0].headers


def test_get_trending_dimensions_calls_countries_endpoint():
    requests = []
    with AdanosClient(
        api_key="sk_live_test",
        transport=_transport(requests, [{"country": "United States"}]),
    ) as client:
        payload = client.news.trending_countries(days=2, source="bloomberg")

    assert payload == [{"country": "United States"}]
    assert requests[0].url.path == "/news/stocks/v1/trending/countries"
    assert dict(requests[0].url.params)["source"] == "bloomberg"


def test_wrapper_dimension_helper_validates_dimension(monkeypatch):
    class DummyClient:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def platform(self, _platform):
            return self

        def trending_sectors(self, **_kwargs):
            return [{"sector": "Technology"}]

        def trending_countries(self, **_kwargs):
            return [{"country": "United States"}]

    monkeypatch.setattr(
        "openbb_adanos.utils.client.AdanosClient",
        lambda *args, **kwargs: DummyClient(),
    )

    assert get_trending_dimensions(
        source="reddit",
        dimension="sectors",
        api_key="sk_live_test",
    ) == [{"sector": "Technology"}]

    with pytest.raises(ValueError, match="dimension must be either 'sectors' or 'countries'"):
        get_trending_dimensions(
            source="reddit",
            dimension="invalid",
            api_key="sk_live_test",
        )


def test_normalize_helpers():
    assert normalize_platform("twitter") == "x"
    assert normalize_symbols("tsla,$nvda,tsla") == ["TSLA", "NVDA"]


def test_resolve_api_key_supports_old_and_new_credential_names(monkeypatch):
    monkeypatch.delenv("OPENBB_ADANOS_API_KEY", raising=False)
    assert resolve_api_key(credentials={"api_key": "sk_live_a"}) == "sk_live_a"
    assert resolve_api_key(credentials={"adanos_adanos_api_key": "sk_live_b"}) == "sk_live_b"

    monkeypatch.setenv("OPENBB_ADANOS_API_KEY", "sk_live_env")
    assert resolve_api_key(required=False) == "sk_live_env"

    monkeypatch.delenv("OPENBB_ADANOS_API_KEY", raising=False)
    with pytest.raises(ValueError, match="Missing Adanos API key"):
        resolve_api_key()
