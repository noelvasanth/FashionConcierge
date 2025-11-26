"""Deterministic outfit assembly helpers."""
from __future__ import annotations

import logging
from typing import Dict, Iterable, List, Sequence

from models.color_theory import (
    analogous_triplet,
    choose_harmonious_colors,
    complementary,
    monochrome,
)
from models.mood_styles import MoodStyleProfile, get_mood_style
from models.wardrobe_item import WardrobeItem
from tools.wardrobe_tools import WardrobeTools

logger = logging.getLogger(__name__)

REQUIRED_CATEGORIES = ("top", "bottom", "shoes")
OPTIONAL_CATEGORIES = ("outerwear", "accessory")


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
) -> List[WardrobeItem]:
    """Filter wardrobe items using mood-aligned styles and palettes."""

    mood_profile = get_mood_style(mood)
    items = _coerce_items(wardrobe_tools.list_wardrobe_items(user_id))
    logger.info("Fetched %s wardrobe items for user=%s", len(items), user_id)

    style_matches = [
        item for item in items if set(item.style_tags).intersection(set(mood_profile.style_tags))
    ]
    if style_matches:
        items = style_matches
        logger.info("Filtered to %s items matching mood style tags %s", len(items), mood_profile.style_tags)
    color_matches = [item for item in items if set(item.colors).intersection(set(mood_profile.palette))]
    if color_matches and _has_required_categories(color_matches):
        items = color_matches
        logger.info("Filtered to %s items matching mood palette %s", len(items), mood_profile.palette)
    elif color_matches:
        logger.info("Skipping palette filter to retain required categories")

    items = _apply_constraints(items, constraints)
    return sorted(items, key=lambda item: item.item_id)


def _score_color_combo(colors: List[str], mood_profile: MoodStyleProfile) -> int:
    harmony = choose_harmonious_colors(colors, mood_profile.palette)
    score = len(harmony)
    if monochrome(colors):
        score += 2
    if len(colors) >= 2 and complementary(colors[0], colors[1]):
        score += 1
    if len(colors) >= 3 and analogous_triplet(colors[:3]):
        score += 1
    return score


def build_outfit(candidate_items: List[WardrobeItem], mood_profile: MoodStyleProfile) -> List[WardrobeItem]:
    """Select a minimal set of items for a coherent outfit."""

    grouped: Dict[str, List[WardrobeItem]] = {category: [] for category in REQUIRED_CATEGORIES + OPTIONAL_CATEGORIES}
    for item in candidate_items:
        if item.category in grouped:
            grouped[item.category].append(item)
    for values in grouped.values():
        values.sort(key=lambda i: i.item_id)

    if not all(grouped[cat] for cat in REQUIRED_CATEGORIES):
        logger.info("Insufficient items for required categories: %s", grouped)
        return []

    best_combo: List[WardrobeItem] = []
    best_score = -1
    for top in grouped["top"]:
        for bottom in grouped["bottom"]:
            for shoes in grouped["shoes"]:
                colors = top.colors + bottom.colors + shoes.colors
                score = _score_color_combo(colors, mood_profile)
                combination = [top, bottom, shoes]
                if score > best_score:
                    best_score = score
                    best_combo = combination
                elif score == best_score:
                    current_ids = [item.item_id for item in best_combo]
                    candidate_ids = [item.item_id for item in combination]
                    if candidate_ids < current_ids:
                        best_combo = combination
    logger.info("Selected base outfit with score=%s", best_score)

    for category in OPTIONAL_CATEGORIES:
        if grouped[category]:
            best_combo.append(grouped[category][0])
            logger.info("Added optional %s item %s", category, grouped[category][0].item_id)
    return best_combo


def apply_color_harmony(outfit_items: List[WardrobeItem], mood_profile: MoodStyleProfile) -> List[WardrobeItem]:
    """Remove optional pieces that clash with the selected harmony."""

    if not outfit_items:
        return []
    base_items = [item for item in outfit_items if item.category in REQUIRED_CATEGORIES]
    optional_items = [item for item in outfit_items if item.category not in REQUIRED_CATEGORIES]
    chosen_colors = choose_harmonious_colors(
        [color for item in base_items for color in item.colors], mood_profile.palette
    )
    harmonised = list(base_items)
    for item in optional_items:
        if set(item.colors).intersection(set(chosen_colors)):
            harmonised.append(item)
            logger.info("Kept optional item %s after harmony check", item.item_id)
        else:
            logger.info("Dropped optional item %s due to color clash", item.item_id)
    return harmonised


def generate_collage_spec(outfit_items: List[WardrobeItem], mood_profile: MoodStyleProfile) -> Dict[str, object]:
    """Create a deterministic collage specification for rendering."""

    stickers = []
    count = len(outfit_items)
    for index, item in enumerate(outfit_items):
        x_position = 0.15 + (index % 3) * 0.3
        y_position = 0.2 + (index // 3) * 0.3
        stickers.append(
            {
                "image_url": item.image_url,
                "x": round(min(x_position, 0.9), 2),
                "y": round(min(y_position, 0.9), 2),
                "scale": 0.8 if count <= 3 else 0.65,
            }
        )
    collage = {"background_color": mood_profile.background_color, "stickers": stickers}
    logger.info("Generated collage with %s stickers", len(stickers))
    return collage


__all__ = [
    "select_candidates_for_mood",
    "build_outfit",
    "apply_color_harmony",
    "generate_collage_spec",
]
