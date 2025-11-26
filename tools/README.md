# Tools and providers

This package holds provider abstractions and ADK tool wrappers that bridge agents to external services or local storage. Tools keep side effects encapsulated and make it easy to swap implementations (e.g., mock vs. live providers).

## Provider interfaces and implementations

- `calendar_provider.py` – Defines the calendar interface and a Google Calendar implementation exposed as an ADK tool. The legacy `calendar.py` path remains as a compatibility shim that re-exports the canonical types.
- `weather_provider.py` – Weather provider interface and a concrete wrapper (e.g., OpenWeather) surfaced as an ADK tool. The legacy `weather.py` path is kept only as a shim for backward compatibility.
- `wardrobe_store.py` – SQLite-backed wardrobe persistence with helper queries.
- `rag.py` – Embedding-aware retrieval helpers over wardrobe items for similarity search.
- `memory_tools.py` – Accessors for user preference storage that are safe to call from agents.
- `wardrobe_tools.py` – Higher-level wardrobe operations exposed to agents (ingest, list, retrieve by filters).
- `product_page_fetcher.py` and `product_parser.py` – Deterministic scraping helpers that extract product metadata and imagery for ingestion.

## Design guidance

- Keep provider interfaces small and typed so new implementations can be dropped in without changing agent logic.
- Prefer tool-level logging and validation to make traces readable when debugging multi-agent flows.
- When adding a new external integration, create a provider interface first, implement it, then wrap it as an ADK tool similar to the existing modules.
