"""Lightweight color harmony helpers for deterministic outfit selection."""
from __future__ import annotations

import logging
from typing import Iterable, List, Sequence

from models.taxonomy import normalize_color_name

logger = logging.getLogger(__name__)

_CANONICAL_COLORS: List[str] = [
    "red",
    "orange",
    "yellow",
    "green",
    "blue",
    "indigo",
    "purple",
    "pink",
    "brown",
    "beige",
    "gray",
    "black",
    "white",
]

_COMPLEMENTARY_PAIRS = {
    ("red", "green"),
    ("blue", "orange"),
    ("yellow", "purple"),
    ("pink", "green"),
    ("black", "white"),
}

_ANALOGOUS_CHAINS: List[Sequence[str]] = [
    ("red", "orange", "yellow"),
    ("orange", "yellow", "green"),
    ("yellow", "green", "blue"),
    ("green", "blue", "indigo"),
    ("blue", "indigo", "purple"),
    ("indigo", "purple", "pink"),
]


def _normalise_colors(colors: Iterable[str]) -> List[str]:
    return [normalize_color_name(color) for color in colors if color]


def monochrome(color_list: Iterable[str]) -> bool:
    """Return True when all provided colors collapse to a single tone."""

    normalized = _normalise_colors(color_list)
    unique_colors = {color for color in normalized if color}
    result = len(unique_colors) <= 1
    logger.debug("monochrome check %s -> %s", unique_colors, result)
    return result


def complementary(color1: str, color2: str) -> bool:
    """Return True when the colors form a complementary pair."""

    c1, c2 = normalize_color_name(color1), normalize_color_name(color2)
    if c1 == c2:
        return False
    result = (c1, c2) in _COMPLEMENTARY_PAIRS or (c2, c1) in _COMPLEMENTARY_PAIRS
    logger.debug("complementary check (%s, %s) -> %s", c1, c2, result)
    return result


def analogous_triplet(colors: Sequence[str]) -> bool:
    """Return True when colors form an analogous triplet on a simple wheel."""

    normalized = _normalise_colors(colors)
    if len(normalized) < 3:
        return False
    triplet = tuple(normalized[:3])
    result = any(all(part == candidate for part, candidate in zip(triplet, chain)) for chain in _ANALOGOUS_CHAINS)
    logger.debug("analogous check %s -> %s", triplet, result)
    return result


def choose_harmonious_colors(candidate_colors_from_items: Iterable[str], mood_palette: Iterable[str]) -> List[str]:
    """Return a ranked list of harmonious colors blending items and mood palette."""

    candidates = _normalise_colors(candidate_colors_from_items)
    palette = _normalise_colors(mood_palette)
    logger.info("Evaluating harmony for candidates=%s palette=%s", candidates, palette)

    scores = {}
    for color in candidates:
        score = 0
        if color in palette:
            score += 2
        if complementary(color, palette[0]) if palette else False:
            score += 1
        scores[color] = score

    if monochrome(candidates):
        for color in candidates:
            scores[color] = scores.get(color, 0) + 2
    if len(candidates) >= 2 and complementary(candidates[0], candidates[1]):
        scores[candidates[0]] = scores.get(candidates[0], 0) + 1
        scores[candidates[1]] = scores.get(candidates[1], 0) + 1
    if len(candidates) >= 3 and analogous_triplet(candidates[:3]):
        for color in candidates[:3]:
            scores[color] = scores.get(color, 0) + 1

    ranked = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
    chosen = [color for color, _ in ranked if color in _CANONICAL_COLORS]
    logger.info("Harmonious colors ranked -> %s", chosen)
    return chosen


__all__ = [
    "monochrome",
    "complementary",
    "analogous_triplet",
    "choose_harmonious_colors",
]
