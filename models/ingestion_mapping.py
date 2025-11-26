"""Mapping logic from raw ingestion metadata to :class:`WardrobeItem`."""

from __future__ import annotations

import logging
import re
import uuid
from typing import Dict, Iterable, List, Tuple

from models.taxonomy import CATEGORIES, normalize_color_name
from models.wardrobe_item import WardrobeItem

logger = logging.getLogger(__name__)


def _flatten_text(raw: Dict[str, object]) -> str:
    text_parts: List[str] = []
    for key in ("title", "description", "brand", "category"):
        value = raw.get(key)
        if isinstance(value, str):
            text_parts.append(value.lower())
    return " ".join(text_parts)


def _infer_category_and_subcategory(raw: Dict[str, object]) -> Tuple[str, str]:
    text = _flatten_text(raw)
    for category, subcategories in CATEGORIES.items():
        for sub in subcategories:
            pattern = rf"\b{sub.replace('_', ' ')}\b"
            if re.search(pattern, text):
                logger.debug(
                    "Matched subcategory from text", extra={"category": category, "sub_category": sub}
                )
                return category, sub

    fallback_category = raw.get("category")
    if isinstance(fallback_category, str) and fallback_category in CATEGORIES:
        subcategory = CATEGORIES[fallback_category][0]
        logger.debug(
            "Using fallback category with default subcategory",
            extra={"category": fallback_category, "sub_category": subcategory},
        )
        return fallback_category, subcategory

    raise ValueError("Unable to infer category and subcategory from metadata")


def _collect_colors(raw: Dict[str, object]) -> List[str]:
    detected: List[str] = []
    for color in raw.get("colors", []) or []:
        normalised = normalize_color_name(str(color))
        if normalised:
            detected.append(normalised)

    text = _flatten_text(raw)
    for color in {normalize_color_name(word) for word in text.split()}:
        if color and color not in detected:
            detected.append(color)
    return detected


def _collect_materials(raw: Dict[str, object]) -> List[str]:
    materials = [str(m).lower() for m in raw.get("materials", []) or [] if str(m).strip()]
    description = _flatten_text(raw)
    for material in ["cotton", "linen", "wool", "denim", "leather", "silk"]:
        if material in description and material not in materials:
            materials.append(material)
    return materials


def _default_style_tags(category: str, sub_category: str) -> List[str]:
    if category == "dress":
        return ["party"]
    if category == "outerwear":
        return ["casual"]
    if sub_category in {"blazer", "shirt"}:
        return ["business"]
    if sub_category in {"sneakers", "hoodie"}:
        return ["street"]
    return ["casual"]


def _default_season_tags(category: str, materials: Iterable[str]) -> List[str]:
    material_set = {m.lower() for m in materials}
    if category == "outerwear" or "wool" in material_set or "puffer" in material_set:
        return ["cold_weather"]
    if "linen" in material_set or "cotton" in material_set:
        return ["warm_weather"]
    return ["all_year"]


def map_raw_metadata_to_wardrobe_item(
    user_id: str, source_url: str, raw: Dict[str, object]
) -> WardrobeItem:
    """Map parsed metadata into a fully validated :class:`WardrobeItem`.

    Raises a :class:`ValueError` if mandatory attributes cannot be inferred.
    """

    category, sub_category = _infer_category_and_subcategory(raw)
    colors = _collect_colors(raw)
    materials = _collect_materials(raw)
    brand = raw.get("brand") if isinstance(raw.get("brand"), str) else None
    image_url = str(raw.get("image_url") or "").strip()
    if not image_url:
        raise ValueError("Missing image URL in parsed metadata")

    item = WardrobeItem(
        item_id=str(uuid.uuid4()),
        user_id=user_id,
        image_url=image_url,
        source_url=source_url,
        category=category,
        sub_category=sub_category,
        colors=colors,
        materials=materials,
        brand=brand,
        fit=None,
        season_tags=_default_season_tags(category, materials),
        style_tags=_default_style_tags(category, sub_category),
    )
    logger.debug(
        "Mapped raw metadata to WardrobeItem",
        extra={
            "user_id": user_id,
            "source_url": source_url,
            "category": category,
            "sub_category": sub_category,
            "colors": item.colors,
            "materials": item.materials,
        },
    )
    return item


__all__ = ["map_raw_metadata_to_wardrobe_item"]
