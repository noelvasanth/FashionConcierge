"""Wardrobe domain models."""

from dataclasses import dataclass, field
from typing import List, Optional


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
