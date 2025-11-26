"""Wardrobe ingestion agent for turning product URLs into WardrobeItems."""

from __future__ import annotations

import logging
from dataclasses import asdict
from typing import Any, Dict, List

from adk_app.genai_fallback import ensure_genai_imports

ensure_genai_imports()

from google.generativeai import agent as genai_agent

from adk_app.config import ADKConfig
from models.ingestion_mapping import map_raw_metadata_to_wardrobe_item
from tools.product_page_fetcher import fetch_product_page
from tools.product_parser import parse_product_html
from tools.wardrobe_tools import WardrobeTools

logger = logging.getLogger(__name__)


class WardrobeIngestionAgent:
    """Ingests retailer URLs and extracts wardrobe items."""

    def __init__(
        self,
        config: ADKConfig,
        wardrobe_tools: WardrobeTools,
        tools: list | None = None,
    ) -> None:
        self.config = config
        self.wardrobe_tools = wardrobe_tools
        ingestion_tools = tools or []
        self.tools = ingestion_tools
        self.system_instruction = (
            "You ingest retailer product pages, extract fashion metadata and store"
            " wardrobe items."
        )
        self._llm_agent = genai_agent.LlmAgent(
            model=self.config.model,
            system_instruction=self.system_instruction,
            name="wardrobe-ingestion",
            tools=self.tools,
        )

    @property
    def adk_agent(self) -> genai_agent.LlmAgent:
        return self._llm_agent

    def ingest(self, user_id: str, urls: List[str]) -> Dict[str, Any]:
        """Fetch, parse and store wardrobe items from retailer URLs."""

        successes: List[Dict[str, Any]] = []
        failures: List[Dict[str, str]] = []

        for url in urls:
            try:
                html = fetch_product_page(url)
                raw = parse_product_html(html, url)
                item = map_raw_metadata_to_wardrobe_item(user_id=user_id, source_url=url, raw=raw)
                stored = self.wardrobe_tools.add_wardrobe_item(user_id=user_id, item_data=asdict(item))
                logger.info(
                    "Stored wardrobe item", extra={"user_id": user_id, "item_id": stored["item_id"], "url": url}
                )
                successes.append(
                    {
                        "item_id": stored["item_id"],
                        "url": url,
                        "category": stored["category"],
                        "sub_category": stored["sub_category"],
                        "image_url": stored["image_url"],
                    }
                )
            except Exception as exc:  # pragma: no cover - defensive catch at agent boundary
                logger.error("Failed to ingest URL", extra={"url": url, "error": str(exc)})
                failures.append({"url": url, "reason": str(exc)})

        return {"items": successes, "failures": failures}
