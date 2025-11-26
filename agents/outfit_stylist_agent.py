"""Outfit stylist agent leveraging deterministic outfit_builder logic."""
from __future__ import annotations

import logging
from typing import Dict, List, Optional

from adk_app.genai_fallback import ensure_genai_imports

ensure_genai_imports()
from google.generativeai import agent as genai_agent  # type: ignore  # noqa: E402

from adk_app.config import ADKConfig
from logic.outfit_builder import (
    apply_color_harmony,
    build_outfit,
    generate_collage_spec,
    select_candidates_for_mood,
)
from models.mood_styles import get_mood_style
from tools.wardrobe_tools import WardrobeTools

logger = logging.getLogger(__name__)


class OutfitStylistAgent:
    """Builds outfits from wardrobe items without relying on LLM selection."""

    def __init__(self, config: ADKConfig, wardrobe_tools: WardrobeTools) -> None:
        self.config = config
        self.wardrobe_tools = wardrobe_tools
        self.system_instruction = (
            "You propose outfits that respect mood and color harmony. Use the provided "
            "tools for wardrobe access and return structured outfit JSON with a collage spec."
        )
        self._llm_agent = self._build_llm_agent()

    def _build_llm_agent(self) -> genai_agent.LlmAgent:
        return genai_agent.LlmAgent(
            model=self.config.model,
            system_instruction=self.system_instruction,
            name="outfit-stylist",
            tools=[
                genai_agent.Tool(
                    name="recommend_outfit",
                    description="Create a deterministic outfit for a user and mood.",
                    func=self.recommend_outfit,
                )
            ],
        )

    @property
    def adk_agent(self) -> genai_agent.LlmAgent:
        return self._llm_agent

    def recommend_outfit(
        self, user_id: str, mood: Optional[str] = None, constraints: Optional[List[str]] = None
    ) -> Dict[str, object]:
        """Return outfit metadata, collage specification and rationale."""

        logger.info("Stylist agent invoked for user=%s mood=%s", user_id, mood)
        mood_profile = get_mood_style(mood)
        candidates = select_candidates_for_mood(user_id, mood, self.wardrobe_tools, constraints or [])
        outfit_items = build_outfit(candidates, mood_profile)
        harmonised_items = apply_color_harmony(outfit_items, mood_profile)
        collage = generate_collage_spec(harmonised_items, mood_profile)

        selected_items = [item.__dict__ for item in harmonised_items]
        rationale = (
            f"Built a {mood_profile.name} outfit using {', '.join([item.category for item in harmonised_items])} "
            f"with colors aligned to {', '.join(mood_profile.palette)}."
        )
        logger.info("Returning %s items for outfit", len(selected_items))
        return {
            "items": selected_items,
            "collage": collage,
            "rationale": rationale,
        }


__all__ = ["OutfitStylistAgent"]
