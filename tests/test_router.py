"""Tests for the OpenBB router extension."""

from __future__ import annotations

from openbb_adanos.router import _to_obbject, router


def test_router_exposes_all_platform_namespaces():
    assert set(router.routers) == {"reddit", "news", "x", "polymarket"}


def test_x_router_exposes_explain_without_polymarket_explain():
    x_routes = {route.operation_id: route.path for route in router.routers["x"].api_router.routes}
    polymarket_routes = {
        route.operation_id: route.path for route in router.routers["polymarket"].api_router.routes
    }

    assert x_routes["x_explain"] == "/explain"
    assert "polymarket_explain" not in polymarket_routes


def test_search_payload_is_normalized_for_dataframe_usage():
    obbject = _to_obbject(
        "reddit",
        "search",
        {
            "query": "tesla",
            "count": 1,
            "period_days": 7,
            "results": [{"ticker": "TSLA", "summary": {"mentions": 123}}],
        },
    )

    assert obbject.results == [{"ticker": "TSLA", "summary": {"mentions": 123}}]
    assert obbject.extra["query"] == "tesla"
    assert obbject.extra["count"] == 1
    assert obbject.extra["period_days"] == 7


def test_compare_payload_is_normalized_for_dataframe_usage():
    obbject = _to_obbject(
        "polymarket",
        "compare",
        {
            "period_days": 7,
            "stocks": [{"ticker": "TSLA", "trade_count": 12}],
        },
    )

    assert obbject.results == [{"ticker": "TSLA", "trade_count": 12}]
    assert obbject.extra["period_days"] == 7
