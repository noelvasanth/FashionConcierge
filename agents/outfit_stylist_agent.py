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
    HarmonyApplicationResult,
    OutfitBuildResult,
    CandidateSelectionResult,
    CollageSpecResult,
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
        candidate_result: CandidateSelectionResult = select_candidates_for_mood(
            user_id, mood, self.wardrobe_tools, constraints or []
        )
        outfit_result: OutfitBuildResult = build_outfit(candidate_result.items, mood_profile)
        harmony_result: HarmonyApplicationResult = apply_color_harmony(outfit_result.items, mood_profile)
        collage_result: CollageSpecResult = generate_collage_spec(harmony_result.items, mood_profile)

        selected_items = [item.__dict__ for item in harmony_result.items]
        logger.info("Returning %s items for outfit", len(selected_items))

        user_facing_rationale = (
            f"Chose a {mood_profile.name} look with a balanced {', '.join(mood_profile.palette)} palette, "
            f"pairing {', '.join([item.category for item in harmony_result.items])} for a complete day-ready outfit. "
            f"Colors harmonise via {harmony_result.diagnostics.get('rule_used', 'balanced')} highlights."
        )
        debug_summary = {
            "filtered_item_counts": {
                "initial": candidate_result.diagnostics.get("initial_count"),
                "style_filtered": candidate_result.diagnostics.get("style_filtered_count"),
                "palette_filtered": candidate_result.diagnostics.get("palette_filtered_count"),
                "final": candidate_result.diagnostics.get("final_count"),
            },
            "applied_filters": candidate_result.diagnostics.get("applied_filters"),
            "color_harmony_rule_used": harmony_result.diagnostics.get("rule_used"),
            "mood_profile_used": candidate_result.diagnostics.get("mood_profile"),
            "build_stats": outfit_result.diagnostics,
            "harmony_colors": harmony_result.diagnostics.get("chosen_colors"),
            "collage": collage_result.diagnostics,
        }
        return {
            "items": selected_items,
            "collage": collage_result.collage,
            "user_facing_rationale": user_facing_rationale,
            "debug_summary": debug_summary,
        }


__all__ = ["OutfitStylistAgent"]
