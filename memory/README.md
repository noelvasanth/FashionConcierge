# Memory

The memory package manages lightweight, transparent user preference storage. The current implementation favors JSON-backed files so users and developers can inspect and edit preferences easily during local development.

## Modules

- `user_profile.py` – Helper functions to load, persist, and update per-user preference files (e.g., favorite colors, fit sensitivities, dress code norms).
- `__init__.py` – Convenience exports for memory helpers.

## Usage

- Agents should call memory helpers via tools defined in `tools/memory_tools.py` to keep IO traceable.
- User profiles are expected to live alongside runtime data in the project directory; ensure the process has write access.
- When evolving the schema, keep defaults backward compatible and document new fields so they appear in the stored JSON.
