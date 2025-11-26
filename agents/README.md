# Agents

The agents package contains the orchestrator and domain-specialized agents used by the Fashion Concierge App. Each agent is an ADK `LlmAgent` configured with targeted tools and prompts to keep responsibilities narrow and testable.

## Agent roster

- `orchestrator.py` – Entry point for user requests. Plans calls to sub-agents based on date, location, and mood, then composes the final response.
- `wardrobe_ingestion.py` – Accepts product URLs, fetches and parses product pages, and stores normalized `WardrobeItem` records.
- `wardrobe_query.py` – Retrieves wardrobe candidates via filtering and RAG search using event, weather, and mood context.
- `calendar_agent.py` – Pulls events via the calendar provider, classifies them, and builds daily schedule profiles.
- `weather_agent.py` – Fetches forecasts and derives clothing guidance (outer layers, rain-friendly footwear, etc.).
- `outfit_stylist_agent.py` – Translate schedule, weather, mood, and wardrobe candidates into outfits; apply fashion and color rules.
- `quality_critic.py` – Optional reviewer that spots conflicts or repetition in proposed outfits.

## Usage notes

- Agents should call tools rather than raw providers to keep tracing and swapping implementations easy.
- Keep prompts focused on the specific domain task for each agent; avoid monolithic logic in the orchestrator.
- When adding a new agent, register it in `adk_app/app.py` and include a small deterministic prompt or helper for testing.
