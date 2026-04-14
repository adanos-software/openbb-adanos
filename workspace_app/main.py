"""OpenBB Workspace backend for Adanos Market Sentiment widgets."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse

from openbb_adanos.utils.client import (
    API_KEY_ENV_VARS,
    AdanosClient,
    normalize_asset_type,
    normalize_platform,
    normalize_symbols,
    resolve_api_key,
)

APP_DIR = Path(__file__).resolve().parent
SETUP_MESSAGE = (
    "Configure the OpenBB Data Connector header `X-API-Key` with your Adanos API key, "
    "or set `ADANOS_API_KEY` / `OPENBB_ADANOS_API_KEY` on this backend."
)

app = FastAPI(
    title="Adanos Market Sentiment Widgets",
    description="OpenBB Workspace widgets for Adanos cross-platform market sentiment.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://pro.openbb.co",
        "https://pro.openbb.dev",
        "https://excel.openbb.co",
        "http://localhost:1420",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _load_json_file(filename: str) -> Any:
    with (APP_DIR / filename).open(encoding="utf-8") as file:
        return json.load(file)


def _request_api_key(request: Request) -> str | None:
    return resolve_api_key(
        api_key=request.headers.get("x-api-key"),
        required=False,
    )


def _client(api_key: str) -> AdanosClient:
    return AdanosClient(api_key=api_key)


def _safe_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return round(float(value), 4)
    except (TypeError, ValueError):
        return None


def _safe_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _first_present(*values: Any) -> Any:
    for value in values:
        if value is not None:
            return value
    return None


def _display_value(value: Any, fallback: str = "n/a") -> str:
    number = _safe_float(value)
    if number is None:
        return fallback
    if number.is_integer():
        return str(int(number))
    return str(number)


def _mentions(item: dict[str, Any]) -> int | None:
    return _safe_int(
        _first_present(
            item.get("mentions"),
            item.get("total_mentions"),
            item.get("trade_count"),
        )
    )


def _sentiment_row(item: dict[str, Any], *, source: str, days: int) -> dict[str, Any]:
    symbol = item.get("ticker") or item.get("symbol") or ""
    sentiment_score = _first_present(item.get("sentiment_score"), item.get("sentiment"))
    unique_posts = _first_present(item.get("unique_posts"), item.get("unique_tweets"))
    return {
        "symbol": str(symbol).upper(),
        "company_name": item.get("company_name"),
        "source": source,
        "days": days,
        "buzz_score": _safe_float(item.get("buzz_score")),
        "sentiment_score": _safe_float(sentiment_score),
        "mentions": _mentions(item),
        "trend": item.get("trend"),
        "bullish_pct": _safe_float(item.get("bullish_pct")),
        "bearish_pct": _safe_float(item.get("bearish_pct")),
        "total_upvotes": _safe_int(item.get("total_upvotes")),
        "unique_posts": _safe_int(unique_posts),
        "subreddit_count": _safe_int(item.get("subreddit_count")),
        "source_count": _safe_int(item.get("source_count")),
        "trade_count": _safe_int(item.get("trade_count")),
        "market_count": _safe_int(item.get("market_count")),
        "unique_traders": _safe_int(item.get("unique_traders")),
        "total_liquidity": _safe_float(item.get("total_liquidity")),
    }


def _handle_api_error(exc: Exception) -> None:
    if isinstance(exc, ValueError):
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if isinstance(exc, httpx.HTTPStatusError):
        detail = exc.response.text or exc.response.reason_phrase
        raise HTTPException(status_code=exc.response.status_code, detail=detail) from exc
    if isinstance(exc, httpx.HTTPError):
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    raise exc


def _normalize_source(source: str) -> str:
    try:
        return normalize_platform(source)
    except ValueError as exc:
        _handle_api_error(exc)
    raise AssertionError("unreachable")


def _normalize_single_symbol(symbol: str) -> str:
    try:
        return normalize_symbols(symbol, max_items=1)[0]
    except ValueError as exc:
        _handle_api_error(exc)
    raise AssertionError("unreachable")


def _normalize_symbol_list(symbols: str) -> list[str]:
    try:
        return normalize_symbols(symbols, max_items=10)
    except ValueError as exc:
        _handle_api_error(exc)
    raise AssertionError("unreachable")


def _normalize_asset_filter(asset_type: str) -> str | None:
    try:
        normalized = normalize_asset_type(asset_type)
    except ValueError as exc:
        _handle_api_error(exc)
    return None if normalized == "all" else normalized


@app.get("/")
def root() -> dict[str, Any]:
    """Return a lightweight health payload for local and OpenBB checks."""
    return {
        "app": "Adanos Market Sentiment Widgets",
        "status": "ok",
        "widgets": "/widgets.json",
        "apps": "/apps.json",
        "apiKeyEnvVars": list(API_KEY_ENV_VARS),
    }


@app.get("/widgets.json")
def get_widgets() -> JSONResponse:
    """Return OpenBB Workspace widget metadata."""
    return JSONResponse(content=_load_json_file("widgets.json"))


@app.get("/apps.json")
def get_apps() -> JSONResponse:
    """Return OpenBB Workspace app layout metadata."""
    return JSONResponse(content=_load_json_file("apps.json"))


@app.get("/setup", response_class=PlainTextResponse)
def setup() -> str:
    """Return setup instructions as markdown."""
    return (
        "# Adanos Market Sentiment Widgets\n\n"
        "This backend adds cross-platform market sentiment widgets for Reddit, News, "
        "X/Twitter, and Polymarket data.\n\n"
        "## API Key\n\n"
        "Add this custom header in OpenBB Workspace Data Connector settings:\n\n"
        "`X-API-Key: sk_live_...`\n\n"
        "For local backend-only testing you can also set `ADANOS_API_KEY` or "
        "`OPENBB_ADANOS_API_KEY` in the backend environment.\n\n"
        "API docs: https://api.adanos.org/docs/\n"
    )


@app.get("/market_sentiment")
def market_sentiment(
    request: Request,
    source: str = Query("reddit", description="reddit, news, x, or polymarket"),
    days: int = Query(7, ge=1, le=90),
) -> list[dict[str, str]]:
    """Return market-level sentiment as OpenBB metric rows."""
    api_key = _request_api_key(request)
    if not api_key:
        return [
            {
                "label": "Adanos API key",
                "value": "Configure",
                "subvalue": SETUP_MESSAGE,
            }
        ]

    platform = _normalize_source(source)
    try:
        with _client(api_key) as client:
            payload = client.platform(platform).market_sentiment(days=days)
    except Exception as exc:
        _handle_api_error(exc)

    return [
        {
            "label": f"{platform.title()} buzz score",
            "value": _display_value(payload.get("buzz_score")),
            "subvalue": f"{days}-day market snapshot",
        },
        {
            "label": "Sentiment score",
            "value": _display_value(
                _first_present(payload.get("sentiment_score"), payload.get("sentiment"))
            ),
            "subvalue": "-1 bearish to +1 bullish",
        },
        {
            "label": "Tracked drivers",
            "value": _display_value(
                _first_present(
                    payload.get("stock_count"),
                    payload.get("total_stocks"),
                    (
                        len(payload["drivers"])
                        if isinstance(payload.get("drivers"), list)
                        else None
                    ),
                )
            ),
            "subvalue": "available symbols or drivers",
        },
    ]


@app.get("/trending")
def trending(
    request: Request,
    source: str = Query("reddit", description="reddit, news, x, or polymarket"),
    days: int = Query(7, ge=1, le=90),
    limit: int = Query(20, ge=1, le=100),
    asset_type: str = Query("stock", description="stock, etf, or all"),
) -> list[dict[str, Any]]:
    """Return trending market sentiment rows for OpenBB tables."""
    api_key = _request_api_key(request)
    if not api_key:
        return []

    platform = _normalize_source(source)
    normalized_asset_type = _normalize_asset_filter(asset_type)
    try:
        with _client(api_key) as client:
            rows = client.platform(platform).trending(
                days=days,
                limit=limit,
                asset_type=normalized_asset_type,
            )
    except Exception as exc:
        _handle_api_error(exc)

    return [_sentiment_row(item, source=platform, days=days) for item in rows]


@app.get("/stock_sentiment")
def stock_sentiment(
    request: Request,
    symbol: str = Query("AAPL"),
    source: str = Query("reddit", description="reddit, news, x, or polymarket"),
    days: int = Query(7, ge=1, le=90),
) -> list[dict[str, Any]]:
    """Return one symbol sentiment row for OpenBB tables."""
    api_key = _request_api_key(request)
    if not api_key:
        return []

    ticker = _normalize_single_symbol(symbol)
    platform = _normalize_source(source)
    try:
        with _client(api_key) as client:
            payload = client.platform(platform).stock(ticker, days=days)
    except Exception as exc:
        _handle_api_error(exc)

    if not payload or payload.get("found") is False:
        return []
    return [_sentiment_row(payload, source=platform, days=days)]


@app.get("/compare")
def compare(
    request: Request,
    symbols: str = Query("AAPL,MSFT,NVDA"),
    source: str = Query("reddit", description="reddit, news, x, or polymarket"),
    days: int = Query(7, ge=1, le=90),
) -> list[dict[str, Any]]:
    """Return multi-symbol sentiment rows for OpenBB tables."""
    api_key = _request_api_key(request)
    if not api_key:
        return []

    tickers = _normalize_symbol_list(symbols)
    platform = _normalize_source(source)
    try:
        with _client(api_key) as client:
            payload = client.platform(platform).compare(tickers, days=days)
    except Exception as exc:
        _handle_api_error(exc)

    rows = payload.get("stocks", []) if isinstance(payload, dict) else []
    return [_sentiment_row(item, source=platform, days=days) for item in rows]
