"""HTML parsing utilities for retailer product pages."""

from __future__ import annotations

import logging
from typing import Dict, List
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from adk_app.genai_fallback import ensure_genai_imports

ensure_genai_imports()

from google.generativeai import agent as genai_agent

logger = logging.getLogger(__name__)


def _get_meta_content(soup: BeautifulSoup, key: str, attr: str = "property") -> str:
    tag = soup.find("meta", attrs={attr: key})
    return tag["content"].strip() if tag and tag.get("content") else ""


def _extract_image_url(soup: BeautifulSoup, base_url: str) -> str:
    og_image = _get_meta_content(soup, "og:image")
    if og_image:
        return urljoin(base_url, og_image)

    link_image = soup.find("link", rel="image_src")
    if link_image and link_image.get("href"):
        return urljoin(base_url, link_image["href"])

    first_img = soup.find("img", src=True)
    if first_img:
        return urljoin(base_url, first_img["src"])

    return ""


def _extract_text_candidates(soup: BeautifulSoup) -> List[str]:
    candidates: List[str] = []
    for selector in [("title", None), ("h1", None), ("h2", None)]:
        tag = soup.find(selector[0]) if selector[1] is None else soup.find(selector[0], selector[1])
        if tag and tag.text:
            candidates.append(tag.text.strip())
    description = _get_meta_content(soup, "og:description") or _get_meta_content(
        soup, "description", attr="name"
    )
    if description:
        candidates.append(description)
    return [text for text in candidates if text]


def parse_product_html(html: str, url: str) -> Dict[str, object]:
    """Parse retailer HTML to extract raw product metadata.

    The parser is intentionally conservative: it prefers structured metadata such
    as Open Graph tags and falls back to simple heuristics on headings and image
    tags when necessary.
    """

    soup = BeautifulSoup(html, "html.parser")
    title = _get_meta_content(soup, "og:title") or next(
        iter(_extract_text_candidates(soup)), ""
    )
    brand = _get_meta_content(soup, "product:brand") or _get_meta_content(
        soup, "og:site_name"
    )
    description_candidates = _extract_text_candidates(soup)
    description = description_candidates[0] if description_candidates else ""

    raw_colors: List[str] = []
    color_meta = _get_meta_content(soup, "product:color") or _get_meta_content(
        soup, "color", attr="name"
    )
    if color_meta:
        raw_colors.append(color_meta)

    materials: List[str] = []
    material_meta = _get_meta_content(soup, "product:material")
    if material_meta:
        materials.append(material_meta)

    image_url = _extract_image_url(soup, base_url=url)

    parsed = {
        "image_url": image_url,
        "title": title,
        "brand": brand,
        "description": description,
        "colors": raw_colors,
        "materials": materials,
        "source_url": url,
    }

    logger.info(
        "Parsed product HTML", extra={"url": url, "fields": {k: bool(v) for k, v in parsed.items()}}
    )
    return parsed


def parse_product_html_tool() -> genai_agent.Tool:
    """Expose :func:`parse_product_html` as an ADK tool."""

    return genai_agent.Tool(
        name="parse_product_html",
        description="Parse raw product HTML to extract basic metadata like image, title and brand.",
        func=parse_product_html,
    )


__all__ = ["parse_product_html", "parse_product_html_tool"]
