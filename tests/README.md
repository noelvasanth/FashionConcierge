# Tests

The pytest suites in this folder exercise the end-to-end ADK wiring as well as focused flows like wardrobe ingestion, styling, and context synthesis. Use these tests to validate changes before wiring new providers or agents.

## Test files

- `test_app_skeleton.py` – Verifies the ADK App builds and exposes the orchestrator entrypoints.
- `test_wardrobe_storage.py` – Covers the SQLite wardrobe store behavior.
- `test_ingestion_phase2.py` – Ensures product parsing and ingestion populate canonical `WardrobeItem` fields.
- `test_phase3_outfit_styling.py` – Checks stylist logic and color harmony guidance.
- `test_phase4_calendar_weather.py` – Asserts calendar and weather agents shape context correctly.
- `test_phase5_context_styling.py` – Validates contextual filtering and styling across full pipeline inputs.
- `phase1_manual_testing.ipynb` – Notebook for exploratory manual checks.

## Running tests

Execute all suites:

```bash
pytest
```

Or run a subset while iterating on a specific capability:

```bash
pytest tests/test_phase3_outfit_styling.py
```
