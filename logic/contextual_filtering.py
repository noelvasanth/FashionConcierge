"""Deterministic filtering functions for weather, formality, movement and mood."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List

from models.mood_styles import MoodStyleProfile, get_mood_style
from models.wardrobe_item import WardrobeItem


@dataclass(frozen=True)
class FilteringResult:
    """Captures the outcome of a single filtering step."""

    items: List[WardrobeItem]
    removed: Dict[str, str]
    debug: Dict[str, object]


def _normalise_materials(materials: Iterable[str]) -> List[str]:
    return [str(material).lower() for material in materials]


def filter_by_weather(items: List[WardrobeItem], weather_profile: Dict[str, object]) -> FilteringResult:
    """Filter wardrobe items using weather-derived rules."""

    removed: Dict[str, str] = {}
    kept: List[WardrobeItem] = []
    precipitation_probability = getattr(weather_profile.get("raw_forecast"), "precipitation_probability", 0.0)
    rain_sensitivity = str(weather_profile.get("rain_sensitivity", "dry")).lower()
    layers_required = str(weather_profile.get("layers_required", "one")).lower()
    very_cold = str(weather_profile.get("temperature_range", "mild")).lower() in {"cold"}

    for item in items:
        reason = None
        if precipitation_probability > 0.5 or rain_sensitivity in {"heavy rain", "light rain"}:
            if item.category == "shoes":
                materials = _normalise_materials(item.materials)
                if any(material in {"suede", "canvas"} for material in materials):
                    reason = "not suitable for precipitation"
        if very_cold and item.category == "top":
            materials = _normalise_materials(item.materials)
            if any(material in {"linen", "thin cotton", "lightweight cotton"} for material in materials):
                reason = "too light for cold weather"
        if reason:
            removed[item.item_id] = reason
        else:
            kept.append(item)

    debug = {
        "input_count": len(items),
        "kept_count": len(kept),
        "removed_count": len(removed),
        "layers_required": layers_required,
        "precipitation_probability": precipitation_probability,
        "cold": very_cold,
    }
    if layers_required in {"two", "two plus", "2", "2+"}:
        debug["outerwear_required"] = True
    return FilteringResult(items=kept, removed=removed, debug=debug)


def filter_by_formality(items: List[WardrobeItem], schedule_profile: Dict[str, object]) -> FilteringResult:
    """Filter items based on schedule formality signals."""

    removed: Dict[str, str] = {}
    kept: List[WardrobeItem] = []
    formality = str(schedule_profile.get("formality", "informal")).lower()
    has_fitness = any(part for part in schedule_profile.get("day_parts", []) if "gym" in part or "fitness" in part)

    for item in items:
        reason = None
        styles = set(item.style_tags)
        if formality == "business":
            if "business" not in styles and ("casual" in styles or item.sub_category in {"hoodie", "tshirt", "sneakers"}):
                reason = "too casual for business"
        elif formality == "informal":
            if item.sub_category in {"suit", "blazer"} or "business" in styles:
                reason = "too formal for informal day"
        if not has_fitness and "sporty" in styles and formality == "business":
            reason = reason or "sporty excluded for business focus"

        if reason:
            removed[item.item_id] = reason
        else:
            kept.append(item)

    debug = {
        "input_count": len(items),
        "kept_count": len(kept),
        "removed_count": len(removed),
        "formality": formality,
        "fitness_present": has_fitness,
    }
    return FilteringResult(items=kept, removed=removed, debug=debug)


def filter_by_movement(items: List[WardrobeItem], schedule_profile: Dict[str, object]) -> FilteringResult:
    """Filter items to respect movement/commute needs."""

    removed: Dict[str, str] = {}
    kept: List[WardrobeItem] = []
    movement = str(schedule_profile.get("movement", "low")).lower()
    for item in items:
        reason = None
        if movement == "high" and item.sub_category == "heels":
            reason = "heels avoided for high movement"
        if reason:
            removed[item.item_id] = reason
        else:
            kept.append(item)

    debug = {
        "input_count": len(items),
        "kept_count": len(kept),
        "removed_count": len(removed),
        "movement": movement,
    }
    return FilteringResult(items=kept, removed=removed, debug=debug)


def filter_by_mood(items: List[WardrobeItem], mood_profile: Dict[str, object] | MoodStyleProfile | str) -> FilteringResult:
    """Filter items so that style tags align with the requested mood."""

    if isinstance(mood_profile, MoodStyleProfile):
        profile = mood_profile
    elif isinstance(mood_profile, dict):
        profile = get_mood_style(mood_profile.get("name"))
    else:
        profile = get_mood_style(mood_profile)
    removed: Dict[str, str] = {}
    kept: List[WardrobeItem] = []
    palette = set(profile.palette)
    style_tags = set(profile.style_tags)
    for item in items:
        reason = None
        overlap = set(item.style_tags).intersection(style_tags)
        if not overlap:
            reason = "style tags do not match mood"
        if reason:
            removed[item.item_id] = reason
            continue
        kept.append(item)

    debug = {
        "input_count": len(items),
        "kept_count": len(kept),
        "removed_count": len(removed),
        "mood": profile.name,
        "palette_soft_preference": list(palette),
    }
    return FilteringResult(items=kept, removed=removed, debug=debug)


__all__ = [
    "filter_by_weather",
    "filter_by_formality",
    "filter_by_movement",
    "filter_by_mood",
    "FilteringResult",
]
