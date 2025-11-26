# Server

The `server` package exposes a minimal FastAPI surface for the Fashion Concierge app. It mirrors the Cloud Run / Vertex Agent Engine deployment path while keeping the focus on backend agents and tools.

## Endpoints
- `GET /healthz` – Lightweight readiness probe returning service status, environment, and model information.
- `POST /sessions` – Creates an ADK session for a given `user_id`, returning `session_id` to thread through subsequent calls.
- `POST /orchestrate/outfit` – Runs the end-to-end outfit planning pipeline (calendar + weather context, wardrobe query, styling, optional critic) for `user_id`, `date`, `location`, and `mood`.
- `POST /orchestrate/context` – Returns only the calendar and weather context for a day without proposing outfits.

## Running locally
```bash
APP_ENV=staging uvicorn server.api:app --host 0.0.0.0 --port 8080
```

## Integration tips
- The `FashionConciergeApp` instance is created once per process in `api.py`; avoid global mutable state elsewhere.
- Keep new endpoints thin: validate inputs with Pydantic and delegate to orchestrator methods so observability and memory stay consistent.
- Prefer adding new API routes only when a backend capability is stable and covered by tests in `tests/` or scenarios in `evaluation/`.
