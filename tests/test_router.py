"""Tests for the OpenBB router extension."""

from __future__ import annotations

from openbb_adanos.router import _to_obbject, router


def test_router_exposes_all_platform_namespaces():
    assert set(router.routers) == {"reddit", "news", "x", "polymarket"}


def test_search_payload_is_normalized_for_dataframe_usage():
    obbject = _to_obbject(
        "reddit",
        "search",
        {
            "query": "tesla",
            "count": 1,
            "results": [{"ticker": "TSLA", "mention_count": 123}],
        },
    )

    assert obbject.results == [{"ticker": "TSLA", "mention_count": 123}]
    assert obbject.extra["query"] == "tesla"
    assert obbject.extra["count"] == 1


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
