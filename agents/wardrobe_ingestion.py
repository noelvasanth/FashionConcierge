"""Wardrobe ingestion agent stub."""

from typing import List

from google.generativeai import agent as genai_agent

from adk_app.config import ADKConfig


class WardrobeIngestionAgent:
    """Ingests retailer URLs and extracts wardrobe items."""

    def __init__(self, config: ADKConfig) -> None:
        self.config = config
        self.system_instruction = (
            "You ingest retailer product pages, extract fashion metadata and store"
            " wardrobe items."
        )
        self._llm_agent = genai_agent.LlmAgent(
            model=self.config.model,
            system_instruction=self.system_instruction,
            name="wardrobe-ingestion",
            tools=[],
        )

    @property
    def adk_agent(self) -> genai_agent.LlmAgent:
        return self._llm_agent

    def ingest(self, urls: List[str]) -> str:
        """Placeholder ingestion hook."""

        return (
            "Ingestion stub: fetched %d url(s). Implement extraction and storage next." % len(urls)
        )
