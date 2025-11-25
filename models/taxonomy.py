"""Canonical taxonomy definitions for wardrobe items.

This module centralises the canonical labels for categories, subcategories and
commonly used tags. Helper functions keep validation logic consistent across
agents, tools and data models.
"""

from typing import Dict, Iterable, List


def _normalize_key(value: str) -> str:
    """Normalise a free-form string into a taxonomy key."""

    return value.strip().lower().replace(" ", "_")


CATEGORIES: Dict[str, List[str]] = {
    "top": ["blazer", "shirt", "tee", "polo", "sweater", "hoodie"],
    "bottom": ["jeans", "chinos", "trousers", "skirt", "shorts"],
    "dress": ["day_dress", "evening_dress", "jumpsuit"],
    "shoes": ["sneakers", "boots", "loafers", "heels", "sandals"],
    "outerwear": ["coat", "jacket", "puffer", "trench"],
    "accessory": ["belt", "bag", "hat", "scarf", "jewellery"],
}

STYLE_TAGS = ["casual", "business", "formal", "party", "street", "sporty"]
SEASON_TAGS = ["warm_weather", "cold_weather", "all_year"]
MOODS = ["happy", "neutral", "trendy", "casual", "festive", "urban"]

MOOD_PALETTES: Dict[str, List[str]] = {
    "happy": ["#fbe7c6", "#ffd972", "#ff9b71"],
    "neutral": ["#f5f5f5", "#d0d4d8", "#9ea3a8"],
    "trendy": ["#a1c4fd", "#c2e9fb", "#d4a5a5"],
    "casual": ["#c8d5b9", "#8fc0a9", "#68b0ab"],
    "festive": ["#f4b942", "#e77f67", "#c44536"],
    "urban": ["#1f1f1f", "#3d3d3d", "#7f8487"],
}

COLOR_MAP = {
    "navy blue": "navy",
    "navy": "navy",
    "light blue": "blue",
    "sky blue": "blue",
    "blue": "blue",
    "black": "black",
    "white": "white",
    "off white": "white",
    "cream": "beige",
    "beige": "beige",
    "tan": "beige",
    "brown": "brown",
    "gray": "gray",
    "grey": "gray",
    "green": "green",
    "olive": "green",
    "red": "red",
    "burgundy": "red",
    "pink": "pink",
    "yellow": "yellow",
    "orange": "orange",
}


def validate_category(value: str) -> str:
    """Validate and normalise a category value.

    Raises a :class:`ValueError` if the category is not part of the canonical
    taxonomy.
    """

    key = _normalize_key(value)
    if key not in CATEGORIES:
        raise ValueError(f"Unsupported category '{value}'. Allowed: {sorted(CATEGORIES)}")
    return key


def validate_subcategory(category: str, value: str) -> str:
    """Validate that a subcategory belongs to the given category."""

    category_key = validate_category(category)
    sub_key = _normalize_key(value)
    if sub_key not in CATEGORIES[category_key]:
        raise ValueError(
            f"Unsupported subcategory '{value}' for category '{category_key}'. "
            f"Allowed: {CATEGORIES[category_key]}"
        )
    return sub_key


def normalize_color_name(raw_string: str) -> str:
    """Map a raw color string to a canonical color name."""

    key = raw_string.strip().lower()
    return COLOR_MAP.get(key, key)


def normalise_tags(values: Iterable[str], allowed: List[str]) -> List[str]:
    """Normalise and deduplicate tags against an allowed set."""

    normalised = []
    seen = set()
    for value in values:
        key = _normalize_key(value)
        if key in allowed and key not in seen:
            normalised.append(key)
            seen.add(key)
    return normalised


__all__ = [
    "CATEGORIES",
    "STYLE_TAGS",
    "SEASON_TAGS",
    "MOODS",
    "MOOD_PALETTES",
    "validate_category",
    "validate_subcategory",
    "normalize_color_name",
    "normalise_tags",
]
