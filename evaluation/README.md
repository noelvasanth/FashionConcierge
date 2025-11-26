# Evaluation

This folder contains lightweight evaluation assets for the Fashion Concierge agents. The goal is to keep quick regression checks close to the code while the system is still evolving.

## Contents

- `scenarios.py` – Fixed wardrobe, schedule, weather, and mood scenarios used to sanity-check reasoning.
- `harness.py` – Helpers for running scenarios and asserting expected properties (e.g., weather-appropriate layers).

## How to use

Run targeted evaluations via pytest to validate deterministic logic before broader changes:

```bash
pytest tests/test_phase3_outfit_styling.py
```

When adding new capabilities, create a scenario that exercises the behavior, extend the harness with checks, and then add/extend a pytest to call into the harness.
