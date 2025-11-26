"""Deterministic scoring for candidate outfits."""

from __future__ import annotations

from typing import Dict, List

from models.color_theory import analogous_triplet, complementary, monochrome
from models.mood_styles import MoodStyleProfile, get_mood_style
from models.wardrobe_item import WardrobeItem

WEIGHTS = {
    "context": 0.25,
    "mood": 0.2,
    "color": 0.2,
    "formality": 0.2,
    "comfort": 0.15,
}


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def calculate_color_harmony_metrics(outfit_items: List[WardrobeItem]) -> Dict[str, object]:
    """Compute simple color harmony metrics using deterministic rules."""

    colors = [color for item in outfit_items for color in item.colors]
    if not colors:
        return {"rule_applied": "none", "harmony_score": 0.0}
    rule_applied = "none"
    harmony_score = 0.4
    if monochrome(colors):
        rule_applied = "monochrome"
        harmony_score = 1.0
    elif len(colors) >= 2 and complementary(colors[0], colors[1]):
        rule_applied = "complementary"
        harmony_score = 0.85
    elif len(colors) >= 3 and analogous_triplet(colors[:3]):
        rule_applied = "analogous"
        harmony_score = 0.75
    else:
        harmony_score = 0.5 if len(set(colors)) <= 3 else 0.35

    return {
        "rule_applied": rule_applied,
        "harmony_score": _clamp(harmony_score),
        "colors": colors,
    }


def _formality_score(outfit_items: List[WardrobeItem], required: str) -> float:
    styles = {tag for item in outfit_items for tag in item.style_tags}
    if required == "business":
        if "business" in styles or "formal" in styles:
            return 1.0
        if "smart" in styles or "smart casual" in styles:
            return 0.8
        return 0.4
    if required in {"informal", "smart casual"}:
        if "casual" in styles or "street" in styles:
            return 1.0
    return 0.6


def _movement_score(outfit_items: List[WardrobeItem], movement: str) -> float:
    if movement != "high":
        return 1.0
    penalties = 0
    for item in outfit_items:
        if item.sub_category == "heels":
            penalties += 1
    return _clamp(1.0 - 0.3 * penalties)


def _warmth_score(outfit_items: List[WardrobeItem], warmth_requirement: str) -> float:
    has_outerwear = any(item.category == "outerwear" for item in outfit_items)
    if warmth_requirement == "high":
        return 1.0 if has_outerwear else 0.5
    if warmth_requirement == "medium":
        return 0.8 if has_outerwear else 0.7
    return 0.7


def _context_score(outfit_items: List[WardrobeItem], daily_context: Dict[str, object]) -> float:
    movement_score = _movement_score(outfit_items, str(daily_context.get("movement_requirement", "low")))
    warmth_score = _warmth_score(outfit_items, str(daily_context.get("warmth_requirement", "medium")))
    return _clamp((movement_score + warmth_score) / 2)


def _mood_alignment(outfit_items: List[WardrobeItem], mood_profile: MoodStyleProfile) -> float:
    style_tags = {tag for item in outfit_items for tag in item.style_tags}
    overlap = style_tags.intersection(set(mood_profile.style_tags))
    return _clamp(len(overlap) / max(1, len(set(mood_profile.style_tags))))


def score_outfit(
    outfit_items: List[WardrobeItem],
    daily_context: Dict[str, object],
    mood_profile: MoodStyleProfile | str,
    color_harmony_metrics: Dict[str, object],
) -> Dict[str, object]:
    """Calculate composite score and sub scores for an outfit."""

    profile = mood_profile if isinstance(mood_profile, MoodStyleProfile) else get_mood_style(str(mood_profile))
    formality_required = str(daily_context.get("formality_requirement", "informal"))

    context_val = _context_score(outfit_items, daily_context)
    mood_val = _mood_alignment(outfit_items, profile)
    color_val = _clamp(float(color_harmony_metrics.get("harmony_score", 0.0)))
    formality_val = _formality_score(outfit_items, formality_required)
    comfort_val = _warmth_score(outfit_items, str(daily_context.get("warmth_requirement", "medium")))

    composite = _clamp(
        context_val * WEIGHTS["context"]
        + mood_val * WEIGHTS["mood"]
        + color_val * WEIGHTS["color"]
        + formality_val * WEIGHTS["formality"]
        + comfort_val * WEIGHTS["comfort"]
    )

    explanation = {
        "context": f"movement {daily_context.get('movement_requirement')} warmth {daily_context.get('warmth_requirement')}",
        "mood": f"mood overlap {mood_val:.2f} with {profile.name}",
        "color": f"harmony {color_harmony_metrics.get('rule_applied')}",
        "formality": f"required {formality_required}",
        "comfort": f"outerwear present: {any(item.category == 'outerwear' for item in outfit_items)}",
    }

    return {
        "composite_score": composite,
        "sub_scores": {
            "context": context_val,
            "mood": mood_val,
            "color": color_val,
            "formality": formality_val,
            "comfort": comfort_val,
        },
        "explanation": explanation,
    }


__all__ = ["score_outfit", "calculate_color_harmony_metrics", "WEIGHTS"]
