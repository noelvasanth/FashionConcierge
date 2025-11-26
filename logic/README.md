# Logic helpers

Deterministic reasoning lives here to keep agents lean and tests repeatable. These modules apply rule-based filtering and scoring to complement LLM-driven steps.

## Modules

- `context_synthesizer.py` – Merges calendar, weather, and mood inputs into contextual directives for the stylist.
- `contextual_filtering.py` – Filters wardrobe items by occasion, seasonality, and weather guidance.
- `outfit_builder.py` – Assembles outfits from candidate items, ensuring required layers and category coverage.
- `outfit_scoring.py` – Ranks outfits using heuristics like color harmony and diversity.

## Usage guidance

- Keep deterministic rules explicit here rather than inside prompts so tests can assert behavior.
- When updating fashion rules, adjust both the filtering and scoring steps to maintain coherent recommendations.
- These helpers are pure Python; prefer passing in already-fetched data instead of embedding IO.
