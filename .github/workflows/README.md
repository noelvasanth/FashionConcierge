# GitHub Actions workflows

Workflows in this folder enforce quality gates for the Fashion Concierge project.

## Current workflow
- `ci.yml` – Runs linting and tests on pushes and pull requests. It installs dependencies, executes the evaluation/regression suites, and surfaces results as PR checks.

## Extending CI
- Add new steps for security scans, docs checks, or build/publish flows as the deployment story expands (e.g., Docker image builds for Cloud Run).
- Keep job names descriptive and ensure caching does not mask failures in model/tool wiring.
- When adding secrets (for example to hit external providers), reference GitHub encrypted secrets and document the expectation here.

## Local parity
- Try to mirror workflow steps locally before pushing (`pip install -e .`, `pytest`), so contributors experience the same gates locally and in CI.
