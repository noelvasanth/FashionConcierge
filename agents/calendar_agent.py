"""Calendar agent that classifies events into a schedule profile."""

from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Dict, List, Tuple

from adk_app.genai_fallback import ensure_genai_imports

ensure_genai_imports()

from google.generativeai import agent as genai_agent

from adk_app.config import ADKConfig
from tools.calendar_provider import CalendarEvent, CalendarProvider

LOGGER = logging.getLogger(__name__)


CATEGORY_KEYWORDS: Dict[str, Tuple[str, ...]] = {
    "meeting": ("meeting", "sync", "call", "1:1", "standup"),
    "work": ("work", "office", "project", "deadline"),
    "social": ("dinner", "drinks", "party", "friends", "lunch"),
    "fitness": ("gym", "yoga", "run", "workout", "pilates"),
    "travel": ("flight", "airport", "train", "commute", "travel"),
    "personal": ("doctor", "appointment", "errand", "personal"),
}


def _sanitize_title(title: str) -> str:
    return title[:20] + ("..." if len(title) > 20 else "")


class CalendarAgent:
    """Classifies calendar events into a deterministic schedule profile."""

    def __init__(self, config: ADKConfig, provider: CalendarProvider) -> None:
        self.config = config
        self.provider = provider
        self.system_instruction = (
            "Call the calendar tool, classify events into categories, and summarize the day."
        )
        self._llm_agent = genai_agent.LlmAgent(
            model=self.config.model,
            system_instruction=self.system_instruction,
            name="calendar-agent",
            tools=[provider.as_tool()],
        )

    @property
    def adk_agent(self) -> genai_agent.LlmAgent:
        return self._llm_agent

    def _classify_event(self, event: CalendarEvent) -> str:
        lower_title = event.title.lower()
        for category, keywords in CATEGORY_KEYWORDS.items():
            if any(keyword in lower_title for keyword in keywords):
                return category
        return "personal"

    def _infer_day_part(self, start_time: datetime, category: str) -> str:
        hour = start_time.hour
        if category == "fitness" and hour < 9:
            return "morning gym"
        if category in {"meeting", "work"}:
            return "office block" if 9 <= hour <= 17 else "evening work"
        if category == "social":
            return "dinner" if hour >= 17 else "lunch"
        if category == "travel":
            return "commute" if hour < 12 else "travel window"
        return "flex"

    def _infer_formality(self, categories: List[str]) -> str:
        if "meeting" in categories or "work" in categories:
            return "business"
        if "social" in categories:
            return "smart casual"
        if "fitness" in categories:
            return "informal"
        return "informal"

    def _infer_movement(self, categories: List[str]) -> str:
        if "fitness" in categories or "travel" in categories:
            return "high"
        if "social" in categories:
            return "medium"
        return "low"

    def get_schedule_profile(self, user_id: str, target_date: date, end_date: date | None = None) -> Dict[str, object]:
        """Fetch events and return schedule classification."""

        end = end_date or target_date
        events = self.provider.get_events(user_id=user_id, start_date=target_date, end_date=end)
        categories: List[str] = []
        day_parts: List[str] = []
        safe_events: List[Dict[str, object]] = []

        for event in events:
            category = self._classify_event(event)
            categories.append(category)
            day_parts.append(self._infer_day_part(event.start_time, category))
            safe_events.append(
                {
                    "title": _sanitize_title(event.title),
                    "start": event.start_time.isoformat(),
                    "end": event.end_time.isoformat(),
                    "category": category,
                    "is_all_day": event.is_all_day,
                }
            )

        formality = self._infer_formality(categories)
        movement = self._infer_movement(categories)
        debug_summary = {
            "number_of_events": len(events),
            "inferred_categories": categories,
            "classification_rules": [
                "keyword mapping: meeting->business, social->smart casual, fitness/travel->movement high",
                "day parts by hour thresholds",
            ],
        }

        user_facing_summary = (
            f"Found {len(events)} events. "
            f"Formality looks {formality}. Movement {movement}. Day parts: {', '.join(sorted(set(day_parts)))}."
        )

        return {
            "user_id": user_id,
            "date_range": {"start": target_date.isoformat(), "end": end.isoformat()},
            "events": safe_events,
            "day_parts": sorted(set(day_parts)),
            "formality": formality,
            "movement": movement,
            "user_facing_summary": user_facing_summary,
            "debug_summary": debug_summary,
        }


__all__ = ["CalendarAgent"]
