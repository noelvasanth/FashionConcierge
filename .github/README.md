# GitHub configuration

This directory holds repository-level automation. It keeps CI/CD wiring visible and documented so contributors can understand how checks run before merging.

## Contents
- `workflows/` – GitHub Actions pipelines invoked on pull requests and pushes. See the nested README for per-workflow details.

## Contribution guidelines
- Treat workflow changes as code changes: open a PR, explain why the automation should change, and ensure the pipelines still pass locally where possible.
- Keep secrets out of workflow files; rely on GitHub encrypted secrets or GCP Workload Identity Federation when invoking cloud resources.
- Align any new automation with the ADK-first, backend-focused goals (tests, evaluation scenarios, linting, and image builds).
