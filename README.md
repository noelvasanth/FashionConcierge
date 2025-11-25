# Fashion Concierge ADK

A scaffold for the Fashion Concierge agent built with the Google Agent Development Kit (ADK)
and Gemini models. The project focuses on a modular, backend-first architecture with clear
agent boundaries and pluggable tools.

## Getting started

1. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

2. Set environment variables for local ADK calls:

- `GOOGLE_API_KEY` for local Gemini calls
- `PROJECT_ID` and `LOCATION` to mirror your Vertex AI setup (defaults are provided)
- `GEMINI_MODEL` to override the default model if desired

3. Run the simple smoke test:

```bash
python main.py
```

The CLI prints the orchestrator's deterministic response to confirm wiring.

## Layout

- `adk_app/`: App wiring and configuration
- `agents/`: Orchestrator and domain agents (ingestion, query, calendar, weather, stylist, critic)
- `tools/`: Provider abstractions and tool wrappers
- `models/`: Domain dataclasses and taxonomies
- `memory/`: JSON-backed user preference storage
- `evaluation/`: Early scenario definitions and smoke-test harness

The current code intentionally uses stubs and placeholders to keep local development light while
matching the master specification for later expansion.
