"""Wardrobe item data model and helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional

from models.taxonomy import (
    SEASON_TAGS,
    STYLE_TAGS,
    normalize_color_name,
    normalise_tags,
    validate_category,
    validate_subcategory,
)


def _ensure_list(value: Any) -> List[Any]:
    """Coerce a scalar or iterable into a list."""

    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return list(value)
    return [value]


def _normalise_colors(values: Iterable[str]) -> List[str]:
    """Normalise color names using the canonical taxonomy mapping."""

    normalised = []
    seen = set()
    for value in values:
        key = normalize_color_name(str(value))
        if key and key not in seen:
            normalised.append(key)
            seen.add(key)
    return normalised


@dataclass
class WardrobeItem:
    """Represents an item in the user's wardrobe."""

    item_id: str
    user_id: str
    image_url: str
    source_url: str
    category: str
    sub_category: str
    colors: List[str] = field(default_factory=list)
    materials: List[str] = field(default_factory=list)
    brand: Optional[str] = None
    fit: Optional[str] = None
    season_tags: List[str] = field(default_factory=list)
    style_tags: List[str] = field(default_factory=list)
    user_notes: Optional[str] = None
    embedding: Optional[List[float]] = None

    def __post_init__(self) -> None:
        self.category = validate_category(self.category)
        self.sub_category = validate_subcategory(self.category, self.sub_category)
        self.colors = _normalise_colors(self.colors)
        self.materials = [str(m).strip() for m in _ensure_list(self.materials) if str(m).strip()]
        self.season_tags = normalise_tags(self.season_tags, SEASON_TAGS)
        self.style_tags = normalise_tags(self.style_tags, STYLE_TAGS)
        if self.embedding is not None:
            self.embedding = [float(value) for value in self.embedding]


def from_raw_metadata(metadata: Dict[str, Any]) -> WardrobeItem:
    """Factory to build a :class:`WardrobeItem` from loose ingestion metadata."""

    required_fields = ["item_id", "user_id", "image_url", "source_url", "category", "sub_category"]
    missing = [field for field in required_fields if not metadata.get(field)]
    if missing:
        raise ValueError(f"Missing required fields for WardrobeItem: {missing}")

    return WardrobeItem(
        item_id=str(metadata["item_id"]),
        user_id=str(metadata["user_id"]),
        image_url=str(metadata["image_url"]),
        source_url=str(metadata["source_url"]),
        category=str(metadata["category"]),
        sub_category=str(metadata["sub_category"]),
        colors=_ensure_list(metadata.get("colors")),
        materials=_ensure_list(metadata.get("materials")),
        brand=metadata.get("brand"),
        fit=metadata.get("fit"),
        season_tags=_ensure_list(metadata.get("season_tags")),
        style_tags=_ensure_list(metadata.get("style_tags")),
        user_notes=metadata.get("user_notes"),
        embedding=metadata.get("embedding"),
    )


__all__ = ["WardrobeItem", "from_raw_metadata"]
