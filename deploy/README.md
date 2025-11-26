# Deployment manifests

This directory contains declarative manifests to run the Fashion Concierge on common GCP surfaces. They accompany the backend-first design: agents and tools stay identical across environments while the runtime surface changes.

## Files
- `cloudrun-service.yaml` – Example Cloud Run service definition for the FastAPI entrypoint in `server/api.py`. Configure container image, min/max instances, and env vars (e.g., `APP_ENV`, `PROJECT_ID`).
- `vertex-agent-engine.yaml` – Sketch configuration for deploying via Vertex AI Agent Engine. It highlights the orchestrator entrypoint, model selection, and tool availability.

## Usage
- Build and push an image (e.g., via Cloud Build or GitHub Actions), then reference that image in `cloudrun-service.yaml` before deploying.
- For Agent Engine, align the manifest with the ADK App wiring in `adk_app/app.py` and ensure all tools are declared with proper scopes.
- Keep secrets in Secret Manager or environment variables; never bake them into manifests.

## Contribution tips
- Update these manifests when adding new environment variables, required scopes, or ports.
- Validate changes with `gcloud beta run services replace` (Cloud Run) or the Agent Engine CLI equivalents in a staging project before promoting to production.
