"""Lightweight evaluation harness for deterministic scenarios."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Dict, List

from agents.calendar_agent import CalendarAgent
from agents.orchestrator import OrchestratorAgent
from agents.outfit_stylist_agent import OutfitStylistAgent
from agents.weather_agent import WeatherAgent
from adk_app.config import ADKConfig
from evaluation.scenarios import EvaluationScenario, SCENARIOS
from models.wardrobe_item import from_raw_metadata
from tools.calendar_provider import MockCalendarProvider
from tools.weather_provider import MockWeatherProvider
from tools.wardrobe_store import SQLiteWardrobeStore
from tools.wardrobe_tools import WardrobeTools


def _seed_wardrobe(store: SQLiteWardrobeStore, user_id: str, items: List[Dict[str, object]]) -> None:
    for item in items:
        store.create_item(from_raw_metadata({**item, "user_id": user_id}))


def _evaluate_expectations(expectations: Dict[str, object], outfits: List[Dict[str, object]]) -> Dict[str, object]:
    checks: Dict[str, bool] = {}
    checks["min_outfits"] = len(outfits) >= int(expectations.get("min_outfits", 1))
    if expectations.get("requires_outerwear"):
        checks["requires_outerwear"] = any(
            any(item.get("category") == "outerwear" for item in outfit.get("items", [])) for outfit in outfits
        )
    if expectations.get("prefer_accessory"):
        checks["prefer_accessory"] = any(
            any(item.get("category") == "accessory" for item in outfit.get("items", [])) for outfit in outfits
        )
    if expectations.get("favor_movement"):
        checks["favor_movement"] = any(
            any(item.get("category") == "shoes" and item.get("sub_category") == "sneakers" for item in outfit.get("items", []))
            for outfit in outfits
        )
    return {"passed": all(checks.values()), "checks": checks}


def run_scenario(scenario: EvaluationScenario, user_id: str = "eval_user") -> Dict[str, object]:
    config = ADKConfig.from_env()
    with TemporaryDirectory() as tmpdir:
        store = SQLiteWardrobeStore(Path(tmpdir) / "wardrobe.db")
        wardrobe_tools = WardrobeTools(store)
        _seed_wardrobe(store, user_id, scenario.wardrobe_items)

        calendar_agent = CalendarAgent(config=config, provider=MockCalendarProvider(events=scenario.calendar_events))
        weather_agent = WeatherAgent(config=config, provider=MockWeatherProvider(profile=scenario.weather_profile))
        stylist_agent = OutfitStylistAgent(config=config, wardrobe_tools=wardrobe_tools)
        orchestrator = OrchestratorAgent(
            config=config,
            stylist_agent=stylist_agent,
            calendar_agent=calendar_agent,
            weather_agent=weather_agent,
        )

        response = orchestrator.plan_outfit(
            user_id=user_id,
            date=scenario.target_date,
            location=scenario.location,
            mood=scenario.mood,
        )
        outfits = response.get("top_outfits", [])
        evaluation = _evaluate_expectations(scenario.expectations, outfits)
        return {
            "scenario": scenario.name,
            "passed": evaluation["passed"],
            "checks": evaluation["checks"],
            "outfit_count": len(outfits),
            "response": response,
        }


def run_evaluation_suite() -> List[Dict[str, object]]:
    return [run_scenario(scenario) for scenario in SCENARIOS]


def run_smoke_checks() -> List[str]:
    results = run_evaluation_suite()
    return [f"{result['scenario']}: {'passed' if result['passed'] else 'failed'}" for result in results]


__all__ = ["run_evaluation_suite", "run_scenario", "run_smoke_checks"]
