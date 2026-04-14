# Implementation Plan: Adanos Market Sentiment

## Build

1. Add `workspace_app/main.py` FastAPI backend.
2. Add `widgets.json` with markdown, metric, and table widget metadata.
3. Add `apps.json` dashboard layout as an OpenBB app array.
4. Add local run docs and requirements.
5. Add pytest coverage for metadata endpoints, no-key behavior, and mocked live data endpoints.

## Validation

1. Run `python -m pytest tests -q` in the OpenBB integration repo.
2. Start `uvicorn workspace_app.main:app --port 7779`.
3. Hit `/`, `/widgets.json`, `/apps.json`, and one data endpoint locally.
4. Add `http://localhost:7779` to OpenBB Workspace Data Connectors with `X-API-Key` for browser validation.
