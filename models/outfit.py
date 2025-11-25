"""Outfit and collage schemas."""

from dataclasses import dataclass, field
from typing import List


@dataclass
class Sticker:
    image_url: str
    x: float
    y: float
    scale: float
    text: str


@dataclass
class OutfitLayout:
    name: str
    occasion: str
    mood: str
    rationale: str
    background_color: str
    stickers: List[Sticker] = field(default_factory=list)
