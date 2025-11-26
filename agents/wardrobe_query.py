"""Wardrobe query agent for fetching wardrobe candidates."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from adk_app.genai_fallback import ensure_genai_imports

ensure_genai_imports()

from google.generativeai import agent as genai_agent

from adk_app.config import ADKConfig
from logic.safety import system_instruction
from logic.contextual_filtering import filter_by_formality, filter_by_mood
from models.mood_styles import get_mood_style
from models.wardrobe_item import WardrobeItem, from_raw_metadata


def _normalise_tag(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    return str(value).strip().lower().replace(" ", "_")


class WardrobeQueryAgent:
    """Retrieves and filters wardrobe items for an event."""

    def __init__(self, config: ADKConfig, tools: list | None = None) -> None:
        self.config = config
        self.tools = tools or []
        self.system_instruction = system_instruction(
            "wardrobe query agent. Use registered wardrobe tools, apply filters, and keep wardrobe URLs redacted."
        )
        self._llm_agent = genai_agent.LlmAgent(
            model=self.config.model,
            system_instruction=self.system_instruction,
            name="wardrobe-query",
            tools=self.tools,
        )
        self.tool_index = {getattr(tool, "name", ""): tool for tool in self.tools}

    @property
    def adk_agent(self) -> genai_agent.LlmAgent:
        return self._llm_agent

    def _call_tool(self, name: str, *args: Any, **kwargs: Any) -> Any:
        tool = self.tool_index.get(name)
        if tool and getattr(tool, "func", None):
            return tool.func(*args, **kwargs)
        return None

    def _has_tool(self, name: str) -> bool:
        tool = self.tool_index.get(name)
        return bool(tool and getattr(tool, "func", None))

    def _coerce_items(self, raw_items: Iterable[Dict[str, Any]], user_id: str) -> List[WardrobeItem]:
        items: List[WardrobeItem] = []
        for raw in raw_items or []:
            payload = {**raw, "user_id": raw.get("user_id", user_id)}
            try:
                items.append(from_raw_metadata(payload))
            except ValueError:
                continue
        return items

    def _filter_by_season(
        self, items: List[WardrobeItem], event_profile: Dict[str, Any], weather_profile: Dict[str, Any] | None
    ) -> List[WardrobeItem]:
        season = _normalise_tag(event_profile.get("season"))
        if not season:
            season = _normalise_tag((weather_profile or {}).get("season"))
        if not season:
            return items

        kept: List[WardrobeItem] = []
        for item in items:
            tags = {tag.strip().lower() for tag in item.season_tags}
            if not tags or "all_year" in tags or season in tags:
                kept.append(item)
        return kept

    def _filter_by_activity(self, items: List[WardrobeItem], activity_type: Optional[str]) -> List[WardrobeItem]:
        if not activity_type:
            return items
        normalized = _normalise_tag(activity_type)
        kept: List[WardrobeItem] = []
        for item in items:
            styles = set(item.style_tags)
            if normalized in {"fitness", "gym", "active", "sport"}:
                if "sporty" in styles or item.sub_category in {"sneakers", "shorts", "leggings"}:
                    kept.append(item)
            elif normalized in {"outdoor", "commute"}:
                if item.category == "shoes" and item.sub_category == "heels":
                    continue
                kept.append(item)
            else:
                kept.append(item)
        return kept

    def _apply_exclusions(
        self,
        items: List[WardrobeItem],
        exclusions: Iterable[str] | None,
        user_preferences: Dict[str, Any] | None,
    ) -> List[WardrobeItem]:
        exclusion_ids = {str(value) for value in (exclusions or [])}
        pref_exclusions = (user_preferences or {}).get("exclude_item_ids") or []
        exclusion_ids.update({str(value) for value in pref_exclusions})
        disliked_colors = {
            _normalise_tag(color) for color in ((user_preferences or {}).get("disliked_colors") or []) if color
        }
        avoid_categories = {
            _normalise_tag(cat) for cat in ((user_preferences or {}).get("avoid_categories") or []) if cat
        }

        kept: List[WardrobeItem] = []
        for item in items:
            if item.item_id in exclusion_ids:
                continue
            if avoid_categories and item.category in avoid_categories:
                continue
            if disliked_colors and any(color in disliked_colors for color in item.colors):
                continue
            kept.append(item)
        return kept

    def query(
        self,
        event_profile: Dict[str, Any] | None,
        user_id: str,
        mood: str | None = None,
        weather_profile: Dict[str, Any] | None = None,
        user_preferences: Dict[str, Any] | None = None,
    ) -> List[str]:
        """Fetch wardrobe items matching the event, weather and mood context."""

        event_profile = event_profile or {}
        user_preferences = user_preferences or {}
        mood_profile = get_mood_style(mood)

        filters: Dict[str, Any] = {}
        style_tags = set(mood_profile.style_tags)
        formality = _normalise_tag(event_profile.get("formality"))
        if formality in {"business", "formal"}:
            style_tags.add(formality)
        if style_tags:
            filters["style_tags"] = sorted(style_tags)

        season = _normalise_tag(event_profile.get("season")) or _normalise_tag((weather_profile or {}).get("season"))
        if season:
            filters["season_tags"] = [season, "all_year"]

        preferred_colors = user_preferences.get("preferred_colors") or []
        if preferred_colors:
            filters["colors"] = preferred_colors

        raw_items = []
        if self._has_tool("search_wardrobe_items"):
            raw_items = self._call_tool("search_wardrobe_items", user_id, filters)
        if not raw_items and self._has_tool("list_wardrobe_items"):
            raw_items = self._call_tool("list_wardrobe_items", user_id)

        candidates = self._coerce_items(raw_items or [], user_id)
        candidates = filter_by_formality(candidates, {"formality": formality or "informal", **event_profile}).items
        candidates = self._filter_by_season(candidates, event_profile, weather_profile)
        candidates = self._filter_by_activity(candidates, event_profile.get("activity_type"))
        candidates = filter_by_mood(candidates, mood_profile).items
        candidates = self._apply_exclusions(candidates, event_profile.get("exclusions"), user_preferences)

        return [item.item_id for item in candidates]
