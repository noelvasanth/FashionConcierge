"""Deterministic context synthesizer combining schedule and weather."""

from __future__ import annotations

from typing import Dict, List


def _warmth_requirement(temperature_range: str) -> str:
    return {
        "cold": "high",
        "cool": "medium",
        "mild": "medium",
        "warm": "low",
        "hot": "low",
    }.get(temperature_range, "medium")


def _weather_risk(rain_sensitivity: str, weather_condition: str) -> str:
    if rain_sensitivity == "heavy rain" or weather_condition in {"rain", "storm"}:
        return "high"
    if rain_sensitivity == "light rain" or weather_condition in {"cloudy"}:
        return "medium"
    return "low"


def synthesize_context(schedule_profile: Dict[str, object], weather_profile: Dict[str, object]) -> Dict[str, object]:
    """Combine schedule and weather signals into a daily context."""

    formality_requirement = schedule_profile.get("formality", "informal")
    movement_requirement = schedule_profile.get("movement", "low")
    temperature_range = weather_profile.get("temperature_range", "mild")
    rain_sensitivity = weather_profile.get("rain_sensitivity", "dry")
    raw_forecast = weather_profile.get("raw_forecast")
    weather_condition = getattr(raw_forecast, "weather_condition", "clear") if raw_forecast else "clear"

    warmth_requirement = _warmth_requirement(temperature_range)
    weather_risk_level = _weather_risk(rain_sensitivity, weather_condition)
    special_constraints: List[str] = []
    if movement_requirement == "high":
        special_constraints.append("prioritize breathable and flexible pieces")
    if weather_risk_level == "high":
        special_constraints.append("include waterproof outer layer")

    debug_summary = {
        "schedule_key_signals": [
            f"formality={formality_requirement}",
            f"movement={movement_requirement}",
            f"day_parts={','.join(schedule_profile.get('day_parts', []))}",
        ],
        "weather_key_signals": [
            f"temp_range={temperature_range}",
            f"rain={rain_sensitivity}",
            f"condition={weather_condition}",
        ],
        "combined_rules_applied": [
            "warmth requirement derived from temperature range thresholds",
            "weather risk derived from rain sensitivity and condition",
            "special constraints added for high movement and high weather risk",
        ],
    }

    return {
        "formality_requirement": formality_requirement,
        "movement_requirement": movement_requirement,
        "warmth_requirement": warmth_requirement,
        "weather_risk_level": weather_risk_level,
        "special_constraints": special_constraints,
        "debug_summary": debug_summary,
    }


__all__ = ["synthesize_context"]
