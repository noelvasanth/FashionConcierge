"""Outfit stylist agent stub."""

from typing import Dict, List

from google.generativeai import agent as genai_agent

from adk_app.config import ADKConfig


class OutfitStylistAgent:
    """Builds outfits from wardrobe items."""

    def __init__(self, config: ADKConfig) -> None:
        self.config = config
        self.system_instruction = (
            "You propose outfits that respect weather, occasion and mood. Return "
            "structured outfit JSON with collage metadata."
        )
        self._llm_agent = genai_agent.LlmAgent(
            model=self.config.model,
            system_instruction=self.system_instruction,
            name="outfit-stylist",
            tools=[],
        )

    @property
    def adk_agent(self) -> genai_agent.LlmAgent:
        return self._llm_agent

    def style(self, schedule_profile: Dict[str, str], weather_profile: Dict[str, str], candidates: List[str]) -> List[Dict[str, str]]:
        """Return placeholder outfits."""

        return [
            {
                "name": "Starter look",
                "items": candidates,
                "rationale": "Stylist stub response pending full rules and RAG integration.",
            }
        ]
