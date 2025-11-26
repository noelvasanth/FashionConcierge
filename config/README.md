# Configuration

This folder centralizes environment-aware configuration for the Fashion Concierge ADK app. Defaults live in `adk_app/config.py`; the YAML overlays here provide explicit values for deployment tiers so agents and tools stay deterministic and auditable.

## Structure
- `environments/` – Environment-specific YAML overlays (for example staging vs production). Each file mirrors the keys used in `adk_app/config.py` such as `project_id`, `location`, `model`, `logging`, and provider toggles.

## Usage
- Set `APP_ENV` to `staging` or `production` so the App loads the matching overlay from `config/environments/`.
- Keep secrets and API keys out of these files; rely on environment variables or Secret Manager instead. Only non-secret defaults or toggles should live here.
- When adding new configuration flags, document them in this README and ensure they thread through `adk_app/app.py` or the relevant tool/agent constructor.

## Guidelines
- Prefer safe defaults: timeouts, retries, and mock providers should be explicit per environment.
- Avoid duplicating values already covered by code defaults; the overlays should only diverge where environments truly differ.
- Treat this directory as code: changes should be reviewed and tested (for example via `APP_ENV=staging python main.py`).
