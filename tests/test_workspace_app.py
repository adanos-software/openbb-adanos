"""Tests for the OpenBB Workspace backend app."""

from __future__ import annotations

from fastapi.testclient import TestClient

from openbb_adanos.utils.client import API_KEY_ENV_VARS
from workspace_app import main as workspace_main


class DummyAdanosClient:
    """Minimal Adanos client double used by workspace endpoint tests."""

    def __init__(self) -> None:
        self.api_key = None
        self.platform_name = None
        self.calls = []

    def bind_key(self, api_key: str) -> "DummyAdanosClient":
        self.api_key = api_key
        return self

    def __enter__(self) -> "DummyAdanosClient":
        return self

    def __exit__(self, *_args):
        return None

    def platform(self, platform: str) -> "DummyAdanosClient":
        self.platform_name = platform
        self.calls.append(("platform", platform))
        return self

    def market_sentiment(self, **kwargs):
        self.calls.append(("market_sentiment", kwargs))
        return {
            "buzz_score": 71.25,
            "sentiment_score": 0.314,
            "drivers": [{"ticker": "AAPL"}, {"ticker": "NVDA"}],
        }

    def trending(self, **kwargs):
        self.calls.append(("trending", kwargs))
        return [
            {
                "ticker": "NVDA",
                "company_name": "NVIDIA Corporation",
                "buzz_score": 88.12345,
                "sentiment_score": 0.52,
                "mentions": 1024,
                "trend": "rising",
                "bullish_pct": 71.0,
                "bearish_pct": 12.3,
                "unique_posts": 203,
            }
        ]

    def stock(self, symbol: str, **kwargs):
        self.calls.append(("stock", symbol, kwargs))
        return {
            "ticker": symbol,
            "company_name": "Apple Inc.",
            "found": True,
            "buzz_score": 64.2,
            "sentiment_score": 0.18,
            "total_mentions": 412,
            "trend": "stable",
        }

    def compare(self, symbols, **kwargs):
        self.calls.append(("compare", symbols, kwargs))
        return {
            "stocks": [
                {"ticker": "AAPL", "buzz_score": 64.2, "mentions": 412},
                {"ticker": "MSFT", "buzz_score": 59.8, "trade_count": 37},
            ]
        }


def _clear_api_key_env(monkeypatch) -> None:
    for env_var in API_KEY_ENV_VARS:
        monkeypatch.delenv(env_var, raising=False)


def test_metadata_endpoints_use_openbb_shapes(monkeypatch):
    _clear_api_key_env(monkeypatch)

    def fail_if_metadata_is_reloaded(_filename):
        raise AssertionError("metadata should be served from module cache")

    monkeypatch.setattr(workspace_main, "_load_json_file", fail_if_metadata_is_reloaded)
    client = TestClient(workspace_main.app)

    widgets = client.get("/widgets.json").json()
    apps = client.get("/apps.json").json()

    assert isinstance(widgets, dict)
    assert {"adanos_setup", "adanos_trending", "adanos_compare"} <= set(widgets)
    assert isinstance(apps, list)
    assert apps[0]["allowCustomization"] is True
    assert apps[0]["groups"][0]["name"] == "Group 1"
    assert apps[0]["prompts"]


def test_missing_api_key_keeps_app_discoverable(monkeypatch):
    _clear_api_key_env(monkeypatch)
    client = TestClient(workspace_main.app)

    setup = client.get("/setup")
    metrics = client.get("/market_sentiment")
    trending = client.get("/trending")

    assert setup.status_code == 200
    assert "X-API-Key" in setup.text
    assert metrics.json()[0]["value"] == "Configure"
    assert trending.status_code == 200
    assert trending.json() == []


def test_trending_uses_openbb_header_and_maps_rows(monkeypatch):
    _clear_api_key_env(monkeypatch)
    dummy_client = DummyAdanosClient()
    monkeypatch.setattr(
        workspace_main,
        "_client",
        lambda api_key: dummy_client.bind_key(api_key),
    )
    client = TestClient(workspace_main.app)

    response = client.get(
        "/trending",
        params={"source": "x", "days": 3, "limit": 5, "asset_type": "all"},
        headers={"X-API-Key": "sk_live_test"},
    )

    assert response.status_code == 200
    assert dummy_client.api_key == "sk_live_test"
    assert ("platform", "x") in dummy_client.calls
    assert ("trending", {"days": 3, "limit": 5, "asset_type": None}) in dummy_client.calls
    assert response.json()[0] == {
        "symbol": "NVDA",
        "company_name": "NVIDIA Corporation",
        "source": "x",
        "days": 3,
        "buzz_score": 88.1235,
        "sentiment_score": 0.52,
        "mentions": 1024,
        "trend": "rising",
        "bullish_pct": 71.0,
        "bearish_pct": 12.3,
        "total_upvotes": None,
        "unique_posts": 203,
        "subreddit_count": None,
        "source_count": None,
        "trade_count": None,
        "market_count": None,
        "unique_traders": None,
        "total_liquidity": None,
    }


def test_market_sentiment_maps_metric_rows(monkeypatch):
    _clear_api_key_env(monkeypatch)
    dummy_client = DummyAdanosClient()
    monkeypatch.setattr(
        workspace_main,
        "_client",
        lambda api_key: dummy_client.bind_key(api_key),
    )
    client = TestClient(workspace_main.app)

    response = client.get(
        "/market_sentiment",
        params={"source": "reddit", "days": 7},
        headers={"X-API-Key": "sk_live_test"},
    )

    assert response.status_code == 200
    assert response.json() == [
        {
            "label": "Reddit buzz score",
            "value": "71.25",
            "subvalue": "7-day market snapshot",
        },
        {
            "label": "Sentiment score",
            "value": "0.314",
            "subvalue": "-1 bearish to +1 bullish",
        },
        {
            "label": "Tracked drivers",
            "value": "2",
            "subvalue": "available symbols or drivers",
        },
    ]


def test_stock_and_compare_endpoints_normalize_rows(monkeypatch):
    _clear_api_key_env(monkeypatch)
    dummy_client = DummyAdanosClient()
    monkeypatch.setattr(
        workspace_main,
        "_client",
        lambda api_key: dummy_client.bind_key(api_key),
    )
    client = TestClient(workspace_main.app)

    stock = client.get(
        "/stock_sentiment",
        params={"symbol": "$aapl", "source": "reddit", "days": 14},
        headers={"X-API-Key": "sk_live_test"},
    )
    compare = client.get(
        "/compare",
        params={"symbols": "aapl,msft,aapl", "source": "polymarket", "days": 7},
        headers={"X-API-Key": "sk_live_test"},
    )

    assert stock.status_code == 200
    assert stock.json()[0]["symbol"] == "AAPL"
    assert ("stock", "AAPL", {"days": 14}) in dummy_client.calls
    assert compare.status_code == 200
    assert [row["symbol"] for row in compare.json()] == ["AAPL", "MSFT"]
    assert ("compare", ["AAPL", "MSFT"], {"days": 7}) in dummy_client.calls


def test_invalid_source_returns_400(monkeypatch):
    _clear_api_key_env(monkeypatch)
    client = TestClient(workspace_main.app)

    response = client.get(
        "/trending",
        params={"source": "invalid"},
        headers={"X-API-Key": "sk_live_test"},
    )

    assert response.status_code == 400
    assert "Unknown platform" in response.json()["detail"]


def test_invalid_symbol_inputs_return_400(monkeypatch):
    _clear_api_key_env(monkeypatch)
    client = TestClient(workspace_main.app)

    stock = client.get(
        "/stock_sentiment",
        params={"symbol": "$", "source": "reddit"},
        headers={"X-API-Key": "sk_live_test"},
    )
    compare = client.get(
        "/compare",
        params={"symbols": "", "source": "reddit"},
        headers={"X-API-Key": "sk_live_test"},
    )

    assert stock.status_code == 400
    assert compare.status_code == 400
    assert "At least one symbol" in stock.json()["detail"]
    assert "At least one symbol" in compare.json()["detail"]
