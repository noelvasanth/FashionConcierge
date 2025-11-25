"""Evaluation harness placeholder."""

from typing import List

from agents.orchestrator import OrchestratorAgent
from adk_app.config import ADKConfig
from evaluation.scenarios import SCENARIOS


def run_smoke_checks() -> List[str]:
    """Run lightweight checks to verify the scaffold works locally."""

    orchestrator = OrchestratorAgent(config=ADKConfig.from_env())
    results = []
    for scenario in SCENARIOS:
        response = orchestrator.handle_message("hello from fashion concierge")
        results.append(f"{scenario.name}: {response['status']}")
    return results
