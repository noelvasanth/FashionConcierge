# Models and taxonomies

The models package defines the data structures and controlled vocabularies that keep wardrobe and outfit reasoning consistent. These modules are intentionally lightweight so they can be shared across agents, tools, and evaluation code.

## Core dataclasses

- `wardrobe_item.py` / `wardrobe.py` – Canonical wardrobe item schema, category enums, and helper methods for serialization.
- `outfit.py` – Structures for outfit candidates, rationales, and collage layout metadata returned to clients.

## Supporting logic

- `taxonomy.py` – Canonical taxonomy for categories, subcategories, style tags, and season tags.
- `mood_styles.py` – Maps supported moods (happy, neutral, trendy, casual, festive, urban) to stylistic tendencies and palettes.
- `color_theory.py` – Color harmony helpers for monochrome/complementary/analogous schemes used by the stylist agent.
- `ingestion_mapping.py` – Normalization helpers for mapping scraped product attributes to canonical taxonomy keys.

## Extension tips

- Keep canonical labels stable; use user-facing display overrides outside of these modules.
- Add new attributes to the dataclasses in a backward-compatible way, then update ingestion and RAG tooling to populate them.
- Reuse these structures in tests and evaluation scenarios to avoid diverging schemas between runtime and fixtures.
