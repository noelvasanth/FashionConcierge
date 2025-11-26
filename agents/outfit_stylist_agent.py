"""Outfit stylist agent leveraging deterministic outfit_builder logic."""
from __future__ import annotations

import logging
from typing import Dict, List, Optional

from adk_app.genai_fallback import ensure_genai_imports

ensure_genai_imports()
from google.generativeai import agent as genai_agent  # type: ignore  # noqa: E402

from adk_app.config import ADKConfig
from logic.contextual_filtering import (
    filter_by_formality,
    filter_by_mood,
    filter_by_movement,
    filter_by_weather,
    FilteringResult,
)
from logic.outfit_builder import generate_collage_spec
from logic.outfit_scoring import calculate_color_harmony_metrics, score_outfit
from logic.safety import system_instruction
from models.mood_styles import MoodStyleProfile, get_mood_style
from tools.wardrobe_tools import WardrobeTools
from models.wardrobe_item import WardrobeItem
from adk_app.logging_config import get_logger, log_event, operation_context

logger = get_logger(__name__)


class OutfitStylistAgent:
    """Builds outfits from wardrobe items without relying on LLM selection."""

    def __init__(self, config: ADKConfig, wardrobe_tools: WardrobeTools) -> None:
        self.config = config
        self.wardrobe_tools = wardrobe_tools
        self.system_instruction = system_instruction(
            "outfit stylist. Respect mood and color harmony, call wardrobe tools safely, and return structured JSON only."
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
                    description="Create deterministic outfit recommendations for a user and mood.",
                    func=self.recommend_outfit,
                )
            ],
        )

    @property
    def adk_agent(self) -> genai_agent.LlmAgent:
        return self._llm_agent

    def recommend_outfit(
        self,
        user_id: str,
        mood: Optional[str] = None,
        constraints: Optional[List[str]] = None,
        schedule_profile: Optional[Dict[str, object]] = None,
        weather_profile: Optional[Dict[str, object]] = None,
        daily_context: Optional[Dict[str, object]] = None,
        top_n: int = 3,
    ) -> Dict[str, object]:
        """Return ranked outfit metadata, collage specifications and rationale."""

        with operation_context("agent:stylist.recommend_outfit", user_id=user_id, mood=mood) as correlation_id:
            log_event(
                logger,
                level=logging.INFO,
                event="agent_call_started",
                agent="stylist",
                method="recommend_outfit",
                correlation_id=correlation_id,
                user_id=user_id,
                mood=mood,
            )
            mood_profile = get_mood_style(mood)
            all_items = self._coerce_items(self.wardrobe_tools.list_wardrobe_items(user_id))
            if not schedule_profile:
                schedule_profile = {"formality": "informal", "movement": "low", "day_parts": []}
            if not weather_profile:
                weather_profile = {
                    "layers_required": "one",
                    "rain_sensitivity": "dry",
                    "temperature_range": "mild",
                }
            if not daily_context:
                daily_context = {
                    "formality_requirement": schedule_profile.get("formality", "informal"),
                    "movement_requirement": schedule_profile.get("movement", "low"),
                    "warmth_requirement": "medium",
                    "weather_risk_level": "low",
                    "special_constraints": constraints or [],
                }

            filter_results = self._apply_filters(all_items, schedule_profile, weather_profile, mood_profile)
            filtered_items = filter_results["items"]
            if constraints:
                filtered_items = [item for item in filtered_items if item.item_id not in set(constraints)]

            candidate_outfits = self._generate_candidate_outfits(filtered_items, daily_context, mood_profile)
            scored_outfits = self._score_and_rank(candidate_outfits, daily_context, mood_profile)
            top_ranked = scored_outfits[: max(1, top_n)]

            debug_summary = {
                "filters": filter_results,
                "candidate_outfits": len(candidate_outfits),
                "ranked_outfits": [
                    {
                        "score": outfit["score"]["composite_score"],
                        "ids": [item.item_id for item in outfit["items"]],
                        "color_rule": outfit["color_harmony"]["rule_applied"],
                    }
                    for outfit in scored_outfits
                ],
                "daily_context": daily_context,
            }

            user_facing_rationale = (
                f"Generated {len(top_ranked)} {mood_profile.name} outfits using movement {daily_context.get('movement_requirement')} "
                f"and formality {daily_context.get('formality_requirement')}."
            )

            response_outfits = []
            for outfit in top_ranked:
                collage = generate_collage_spec(outfit["items"], mood_profile)
                response_outfits.append(
                    {
                        "items": [item.__dict__ for item in outfit["items"]],
                        "composite_score": outfit["score"]["composite_score"],
                        "sub_scores": outfit["score"]["sub_scores"],
                        "collage": collage.collage,
                        "color_harmony": outfit["color_harmony"],
                        "rationale": outfit["score"]["explanation"],
                    }
                )

            response = {
                "ranked_outfits": response_outfits,
                "user_facing_rationale": user_facing_rationale,
                "debug_summary": debug_summary,
            }

            log_event(
                logger,
                level=logging.INFO,
                event="agent_call_completed",
                agent="stylist",
                method="recommend_outfit",
                correlation_id=correlation_id,
                outfit_count=len(response_outfits),
                filters=filter_results.get("final_count"),
            )
            return response

    def _coerce_items(self, raw_items: List[Dict[str, object]]) -> List[WardrobeItem]:
        items: List[WardrobeItem] = []
        for raw in raw_items:
            try:
                items.append(WardrobeItem(**raw))
            except Exception as exc:  # noqa: BLE001
                logger.warning("Skipping wardrobe entry due to validation error: %s", exc)
        return sorted(items, key=lambda i: i.item_id)

    def _apply_filters(
        self,
        items: List[WardrobeItem],
        schedule_profile: Dict[str, object],
        weather_profile: Dict[str, object],
        mood_profile: MoodStyleProfile,
    ) -> Dict[str, object]:
        reasons: Dict[str, str] = {}
        debug_steps: List[Dict[str, object]] = []
        filtered = items

        steps = [
            ("weather", filter_by_weather, weather_profile),
            ("formality", filter_by_formality, schedule_profile),
            ("movement", filter_by_movement, schedule_profile),
            ("mood", filter_by_mood, mood_profile),
        ]
        for name, func, context in steps:
            result: FilteringResult = func(filtered, context)  # type: ignore[arg-type]
            reasons.update(result.removed)
            debug_steps.append({"step": name, "debug": result.debug, "removed": result.removed})
            filtered = result.items

        return {"items": filtered, "steps": debug_steps, "reasons": reasons, "final_count": len(filtered)}

    def _generate_candidate_outfits(
        self,
        items: List[WardrobeItem],
        daily_context: Dict[str, object],
        mood_profile: MoodStyleProfile,
    ) -> List[List[WardrobeItem]]:
        grouped: Dict[str, List[WardrobeItem]] = {category: [] for category in ["top", "bottom", "shoes", "outerwear", "accessory"]}
        for item in items:
            if item.category in grouped:
                grouped[item.category].append(item)
        for values in grouped.values():
            values.sort(key=lambda i: i.item_id)

        if not (grouped["top"] and grouped["bottom"] and grouped["shoes"]):
            return []

        outfits: List[List[WardrobeItem]] = []
        outerwear_needed = daily_context.get("warmth_requirement") == "high"

        for top in grouped["top"][:4]:
            for bottom in grouped["bottom"][:4]:
                for shoes in grouped["shoes"][:4]:
                    combo = [top, bottom, shoes]
                    if outerwear_needed and grouped["outerwear"]:
                        combo.append(grouped["outerwear"][0])
                    elif grouped["outerwear"]:
                        combo.append(grouped["outerwear"][0])
                    if grouped["accessory"]:
                        combo.append(grouped["accessory"][0])
                    outfits.append(combo)
                    if len(outfits) >= 12:
                        return outfits
        return outfits

    def _score_and_rank(
        self,
        candidate_outfits: List[List[WardrobeItem]],
        daily_context: Dict[str, object],
        mood_profile: MoodStyleProfile,
    ) -> List[Dict[str, object]]:
        scored: List[Dict[str, object]] = []
        for outfit in candidate_outfits:
            color_metrics = calculate_color_harmony_metrics(outfit)
            score = score_outfit(outfit, daily_context, mood_profile, color_metrics)
            scored.append({"items": outfit, "color_harmony": color_metrics, "score": score})
        scored.sort(key=lambda entry: (-entry["score"]["composite_score"], [item.item_id for item in entry["items"]]))
        return scored


__all__ = ["OutfitStylistAgent"]
