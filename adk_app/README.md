# ADK App wiring

This package holds the application entrypoint for the Google Agent Development Kit (ADK) setup. The `App` instance wires agents and tools together so the orchestrator can delegate work cleanly.

## Key modules

- `app.py` – Builds the ADK `App`, registers the orchestrator and sub-agents, and exposes a `run_orchestrator` helper for CLI/testing.
- `config.py` – Central location for model, project, and location defaults. Environment variables override these values at runtime.
- `genai_fallback.py` – Lightweight Gemini client wrapper used when the full Vertex stack is not available locally.

## Typical flow

1. The CLI (`main.py`) calls `run_orchestrator` to initialize the App and create a session.
2. Tools for calendar, weather, wardrobe storage, RAG, and memory are registered against the App before agents are added.
3. The orchestrator agent receives the user request and dispatches to the specialized agents, each of which calls tools through ADK bindings rather than direct APIs.

## Extending the App

- Add new providers or agents by importing them in `app.py` and registering them on the App instance.
- Keep configuration values centralized in `config.py` to make deployments consistent.
- When adding new tools, prefer thin wrappers that adapt provider interfaces to ADK tool signatures for observability and testing.
