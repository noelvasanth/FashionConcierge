"""Deterministic outfit assembly helpers with transparent diagnostics."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence, Tuple

from models.color_theory import (
    analogous_triplet,
    choose_harmonious_colors,
    complementary,
    HarmonyResult,
    monochrome,
)
from models.mood_styles import MoodStyleProfile, get_mood_style
from models.wardrobe_item import WardrobeItem
from tools.wardrobe_tools import WardrobeTools

logger = logging.getLogger(__name__)

REQUIRED_CATEGORIES = ("top", "bottom", "shoes")
OPTIONAL_CATEGORIES = ("outerwear", "accessory")


@dataclass(frozen=True)
class CandidateSelectionResult:
    items: List[WardrobeItem]
    diagnostics: Dict[str, object]


@dataclass(frozen=True)
class OutfitBuildResult:
    items: List[WardrobeItem]
    diagnostics: Dict[str, object]


@dataclass(frozen=True)
class HarmonyApplicationResult:
    items: List[WardrobeItem]
    diagnostics: Dict[str, object]


@dataclass(frozen=True)
class CollageSpecResult:
    collage: Dict[str, object]
    diagnostics: Dict[str, object]


def _has_required_categories(items: List[WardrobeItem]) -> bool:
    categories = {item.category for item in items}
    return all(category in categories for category in REQUIRED_CATEGORIES)


def _coerce_items(raw_items: Iterable[Dict[str, object]]) -> List[WardrobeItem]:
    items = []
    for raw in raw_items:
        try:
            items.append(WardrobeItem(**raw))
        except Exception as exc:  # noqa: BLE001
            logger.warning("Skipping wardrobe entry due to validation error: %s", exc)
    return items


def _apply_constraints(items: List[WardrobeItem], constraints: Sequence[str] | None) -> List[WardrobeItem]:
    if not constraints:
        return items
    filtered = []
    constraint_text = " ".join(constraints).lower()
    for item in items:
        if "avoid heels" in constraint_text and item.sub_category == "heels":
            continue
        if "prefer pants" in constraint_text and item.sub_category in {"skirt", "shorts"}:
            continue
        filtered.append(item)
    logger.info("Applied constraints '%s' -> %s items", constraint_text, len(filtered))
    return filtered


def select_candidates_for_mood(
    user_id: str, mood: str | None, wardrobe_tools: WardrobeTools, constraints: Sequence[str] | None = None
) -> CandidateSelectionResult:
    """Filter wardrobe items using mood-aligned styles and palettes with diagnostics."""

    mood_profile = get_mood_style(mood)
    items = _coerce_items(wardrobe_tools.list_wardrobe_items(user_id))
    diagnostics: Dict[str, object] = {
        "mood_profile": mood_profile.name,
        "initial_count": len(items),
        "applied_filters": [],
    }
    logger.info("Fetched %s wardrobe items for user=%s", len(items), user_id)

    style_matches = [
        item for item in items if set(item.style_tags).intersection(set(mood_profile.style_tags))
    ]
    diagnostics["style_filtered_count"] = len(style_matches)
    if style_matches:
        items = style_matches
        diagnostics["applied_filters"].append(
            {"type": "style_tags", "values": mood_profile.style_tags}
        )
        logger.info("Filtered to %s items matching mood style tags %s", len(items), mood_profile.style_tags)
    color_matches = [item for item in items if set(item.colors).intersection(set(mood_profile.palette))]
    diagnostics["palette_filtered_count"] = len(color_matches)
    if color_matches and _has_required_categories(color_matches):
        items = color_matches
        diagnostics["applied_filters"].append({"type": "palette", "values": mood_profile.palette})
        logger.info("Filtered to %s items matching mood palette %s", len(items), mood_profile.palette)
    elif color_matches:
        logger.info("Skipping palette filter to retain required categories")

    items = _apply_constraints(items, constraints)
    diagnostics["constraints"] = constraints or []
    diagnostics["final_count"] = len(items)
    return CandidateSelectionResult(items=sorted(items, key=lambda item: item.item_id), diagnostics=diagnostics)


def _score_color_combo(colors: List[str], mood_profile: MoodStyleProfile) -> Tuple[int, HarmonyResult]:
    harmony = choose_harmonious_colors(colors, mood_profile.palette)
    score = len(harmony.chosen_colors)
    if monochrome(colors):
        score += 2
    if len(colors) >= 2 and complementary(colors[0], colors[1]):
        score += 1
    if len(colors) >= 3 and analogous_triplet(colors[:3]):
        score += 1
    return score, harmony


def build_outfit(candidate_items: List[WardrobeItem], mood_profile: MoodStyleProfile) -> OutfitBuildResult:
    """Select a minimal set of items for a coherent outfit with diagnostics."""

    grouped: Dict[str, List[WardrobeItem]] = {category: [] for category in REQUIRED_CATEGORIES + OPTIONAL_CATEGORIES}
    for item in candidate_items:
        if item.category in grouped:
            grouped[item.category].append(item)
    for values in grouped.values():
        values.sort(key=lambda i: i.item_id)

    diagnostics: Dict[str, object] = {
        "combinations_scored": 0,
        "best_score": None,
        "chosen_ids": [],
    }

    if not all(grouped[cat] for cat in REQUIRED_CATEGORIES):
        logger.info("Insufficient items for required categories: %s", grouped)
        diagnostics["reason"] = "missing_required_categories"
        return OutfitBuildResult(items=[], diagnostics=diagnostics)

    best_combo: List[WardrobeItem] = []
    best_score = -1
    best_harmony_rule = "none"
    for top in grouped["top"]:
        for bottom in grouped["bottom"]:
            for shoes in grouped["shoes"]:
                colors = top.colors + bottom.colors + shoes.colors
                score, harmony = _score_color_combo(colors, mood_profile)
                diagnostics["combinations_scored"] = diagnostics.get("combinations_scored", 0) + 1
                combination = [top, bottom, shoes]
                if score > best_score:
                    best_score = score
                    best_combo = combination
                    best_harmony_rule = harmony.rule_used
                elif score == best_score:
                    current_ids = [item.item_id for item in best_combo]
                    candidate_ids = [item.item_id for item in combination]
                    if candidate_ids < current_ids:
                        best_combo = combination
                        best_harmony_rule = harmony.rule_used
    logger.info("Selected base outfit with score=%s", best_score)
    diagnostics["best_score"] = best_score
    diagnostics["harmony_rule"] = best_harmony_rule

    for category in OPTIONAL_CATEGORIES:
        if grouped[category]:
            best_combo.append(grouped[category][0])
            logger.info("Added optional %s item %s", category, grouped[category][0].item_id)
    diagnostics["chosen_ids"] = [item.item_id for item in best_combo]
    return OutfitBuildResult(items=best_combo, diagnostics=diagnostics)


def apply_color_harmony(
    outfit_items: List[WardrobeItem], mood_profile: MoodStyleProfile
) -> HarmonyApplicationResult:
    """Remove optional pieces that clash with the selected harmony."""

    if not outfit_items:
        return HarmonyApplicationResult(items=[], diagnostics={"rule_used": "none"})
    base_items = [item for item in outfit_items if item.category in REQUIRED_CATEGORIES]
    optional_items = [item for item in outfit_items if item.category not in REQUIRED_CATEGORIES]
    harmony_result = choose_harmonious_colors(
        [color for item in base_items for color in item.colors], mood_profile.palette
    )
    harmonised = list(base_items)
    removed: List[str] = []
    kept: List[str] = [item.item_id for item in base_items]
    for item in optional_items:
        if set(item.colors).intersection(set(harmony_result.chosen_colors)):
            harmonised.append(item)
            kept.append(item.item_id)
            logger.info("Kept optional item %s after harmony check", item.item_id)
        else:
            removed.append(item.item_id)
            logger.info("Dropped optional item %s due to color clash", item.item_id)
    diagnostics = {
        "rule_used": harmony_result.rule_used,
        "chosen_colors": harmony_result.chosen_colors,
        "kept": kept,
        "removed": removed,
    }
    return HarmonyApplicationResult(items=harmonised, diagnostics=diagnostics)


def generate_collage_spec(
    outfit_items: List[WardrobeItem], mood_profile: MoodStyleProfile
) -> CollageSpecResult:
    """Create a deterministic collage specification for rendering."""

    stickers = []
    count = len(outfit_items)
    layout_trace = []
    for index, item in enumerate(outfit_items):
        x_position = 0.15 + (index % 3) * 0.3
        y_position = 0.2 + (index // 3) * 0.3
        sticker = {
            "image_url": item.image_url,
            "x": round(min(x_position, 0.9), 2),
            "y": round(min(y_position, 0.9), 2),
            "scale": 0.8 if count <= 3 else 0.65,
        }
        stickers.append(sticker)
        layout_trace.append({"item_id": item.item_id, "x": sticker["x"], "y": sticker["y"]})
    collage = {"background_color": mood_profile.background_color, "stickers": stickers}
    logger.info("Generated collage with %s stickers", len(stickers))
    return CollageSpecResult(
        collage=collage,
        diagnostics={"layout": layout_trace, "background_color": mood_profile.background_color},
    )


__all__ = [
    "select_candidates_for_mood",
    "build_outfit",
    "apply_color_harmony",
    "generate_collage_spec",
    "CandidateSelectionResult",
    "OutfitBuildResult",
    "HarmonyApplicationResult",
    "CollageSpecResult",
]
