# Environment overlays

Environment overlays refine the base settings defined in `adk_app/config.py`. Each YAML file here is intentionally small and only overrides the values that differ by environment.

## Files
- `staging.yaml` – Safer defaults for preview deployments (mock providers on, verbose logging, reduced timeouts, evaluation gates enabled).
- `production.yaml` – Real provider toggles and conservative logging settings suitable for Cloud Run or Vertex AI Agent Engine.

## How it works
- At startup the App reads `APP_ENV` (defaults to `local`) and, when present, loads the matching YAML to merge with code defaults.
- Overlays should stay declarative: avoid secrets and keep them limited to scalar configuration flags.

## Adding a new environment
1. Copy the closest existing YAML as a template.
2. Adjust provider toggles (e.g., enable OpenWeather), logging verbosity, and evaluation strictness.
3. Document the new environment and verify startup via `APP_ENV=<env> python main.py` or `uvicorn server.api:app`.
