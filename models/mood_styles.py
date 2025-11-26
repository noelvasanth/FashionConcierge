"""Mappings between mood themes and stylistic guidance."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List

from models.taxonomy import MOODS, normalize_color_name

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MoodStyleProfile:
    """Represents styling preferences for a given mood."""

    name: str
    style_tags: List[str]
    palette: List[str]
    background_color: str


_MOOD_STYLES: Dict[str, MoodStyleProfile] = {
    "happy": MoodStyleProfile(
        name="happy",
        style_tags=["casual", "party"],
        palette=["yellow", "coral", "pink"],
        background_color="#FFF2CC",
    ),
    "neutral": MoodStyleProfile(
        name="neutral",
        style_tags=["casual", "business"],
        palette=["beige", "gray", "white"],
        background_color="#F5F5F5",
    ),
    "trendy": MoodStyleProfile(
        name="trendy",
        style_tags=["street", "party"],
        palette=["black", "white", "blue"],
        background_color="#E1E8FF",
    ),
    "casual": MoodStyleProfile(
        name="casual",
        style_tags=["casual", "street"],
        palette=["green", "blue", "white"],
        background_color="#E4F2E7",
    ),
    "festive": MoodStyleProfile(
        name="festive",
        style_tags=["party", "trendy"],
        palette=["red", "gold", "black"],
        background_color="#FFD6A5",
    ),
    "urban": MoodStyleProfile(
        name="urban",
        style_tags=["street", "casual"],
        palette=["black", "gray", "white"],
        background_color="#DDE1E4",
    ),
}


def get_mood_style(mood: str | None) -> MoodStyleProfile:
    """Return a :class:`MoodStyleProfile` for the given mood.

    Defaults to the ``neutral`` profile when an unsupported mood is provided.
    """

    normalized = (mood or "").strip().lower()
    if normalized not in _MOOD_STYLES:
        logger.info("Unknown mood '%s', defaulting to neutral profile", mood)
        normalized = "neutral"
    if normalized not in MOODS:
        logger.info("Mood '%s' not part of taxonomy, using neutral fallback", normalized)
        normalized = "neutral"
    profile = _MOOD_STYLES.get(normalized, _MOOD_STYLES["neutral"])
    palette = [normalize_color_name(color) for color in profile.palette]
    if profile.palette != palette:
        logger.debug("Normalised palette %s to %s", profile.palette, palette)
    return MoodStyleProfile(
        name=profile.name,
        style_tags=list(profile.style_tags),
        palette=palette,
        background_color=profile.background_color,
    )


__all__ = ["MoodStyleProfile", "get_mood_style"]
