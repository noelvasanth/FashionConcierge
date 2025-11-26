# Fashion Concierge ADK

This repository implements a backend-first Fashion Concierge powered by the Google Agent Development Kit (ADK) and Gemini models. The system uses a modular multi-agent design so each capability (calendar, weather, wardrobe ingestion/query, styling, quality critique) remains testable and replaceable. The code favors clear interfaces, local development ergonomics, and observability over UI polish.

## Quick start

1. Create and activate a virtual environment, then install the project in editable mode:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

2. Export the minimal environment variables for ADK and Vertex-compatible calls:

- `GOOGLE_API_KEY` (required for local Gemini calls)
- `PROJECT_ID` and `LOCATION` (optional; defaults exist in `adk_app/config.py`)
- `GEMINI_MODEL` (optional override of the default Gemini model)

3. Run the orchestrator smoke test to verify wiring:

```bash
python main.py
```

The CLI prints a deterministic orchestrator response to confirm the ADK App, agents, and tools load correctly.

### Lightweight API server

Run the FastAPI deployment surface locally to mirror the Cloud Run entrypoint:

```bash
APP_ENV=staging uvicorn server.api:app --host 0.0.0.0 --port 8080
```

POST to `/sessions` to open a session, then POST to `/orchestrate/outfit` with `user_id`, `date`, `location`, and `mood` to receive ranked outfits.

## Project layout

- `adk_app/` – ADK App wiring, configuration defaults, and Gemini fallback helper.
- `agents/` – Orchestrator plus domain-specific agents (ingestion, query, calendar, weather, stylist, critic). The canonical stylist lives in `outfit_stylist_agent.py`.
- `tools/` – Provider abstractions and ADK tool wrappers (calendar, weather, wardrobe store, RAG, product parsing, memory).
- `models/` – Dataclasses and canonical taxonomies for wardrobes, outfits, moods, and color theory.
- `logic/` – Deterministic reasoning utilities for outfit filtering, building, scoring, and context synthesis.
- `memory/` – JSON-backed user profile helpers that surface preferences and history to agents.
- `evaluation/` – Scenario definitions and a harness for lightweight regression checks.
- `tests/` – Pytest suites covering app scaffolding, wardrobe storage, ingestion, styling, and context application.
- `bs4/` – Minimal offline stand-in for BeautifulSoup used by product parsing tools.

## Development principles

- **Backend first**: Keep UI minimal; focus on clear agents, tools, and storage interfaces.
- **Modular agents**: Use multiple `LlmAgent` instances orchestrated by a root planner rather than a single monolith.
- **Pluggable providers**: Calendar, weather, wardrobe storage, and RAG live behind provider interfaces for swapability.
- **Deterministic helpers**: Local parsing, taxonomy, and filtering logic enforce safety and reproducibility.
- **Observability**: Favor explicit logging and traceability for agent and tool calls.

## Privacy and data handling

- **Per-user isolation**: Wardrobe items, sessions, and profiles are stored under `data/` using user-specific keys. JSON session stores keep one file per session, while SQLite stores enforce user_id columns to separate tenants.
- **Controlled access**: Agents call providers through validated ADK tools (calendar, weather, wardrobe). Tool decorators validate payloads and reject malformed or cross-user requests before execution.
- **PII-safe logging**: Structured logging applies automatic redaction of user identifiers, URLs, and calendar or wardrobe details. Logs default to summaries and avoid emitting raw event titles, locations, or source links.
- **Fail-safe validation**: Pydantic schemas guard agent inputs/outputs and tool payloads. Schema violations surface `needs_review` responses so a human can triage instead of silently proceeding with questionable data.

## Working on the codebase

- Start at `adk_app/app.py` to see how the App registers agents and tools.
- Consult each folder README for deeper guidance on the modules inside.
- Add new capabilities by extending provider interfaces or introducing new agents, then register them in the App.
- Run targeted tests (for example `pytest tests/test_app_skeleton.py`) while iterating; full suites cover ingestion through styling.

The repository is intentionally lightweight but faithful to the broader specification so additional data sources or richer memory systems can be added without restructuring the agents.
