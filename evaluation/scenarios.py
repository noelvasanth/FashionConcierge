"""Tiny evaluation harness scaffolding."""

from dataclasses import dataclass
from typing import Dict


@dataclass
class EvaluationScenario:
    name: str
    description: str
    wardrobe: Dict[str, str]
    calendar: Dict[str, str]
    weather: Dict[str, str]
    mood: str


SCENARIOS = [
    EvaluationScenario(
        name="sunny_commute",
        description="User commutes to the office on a mild day",
        wardrobe={"items": 5},
        calendar={"profile": "office"},
        weather={"profile": "mild"},
        mood="casual",
    )
]
