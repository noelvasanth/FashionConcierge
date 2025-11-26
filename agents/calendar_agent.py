"""Calendar agent that classifies events into a schedule profile."""

from __future__ import annotations

from datetime import date, datetime
from typing import Dict, List, Tuple

from adk_app.genai_fallback import ensure_genai_imports

ensure_genai_imports()

from google.generativeai import agent as genai_agent

import logging

from adk_app.config import ADKConfig
from adk_app.logging_config import get_logger, log_event, operation_context
from logic.safety import system_instruction
from tools.calendar_provider import CalendarEvent, CalendarProvider
from memory.session_store import SessionManager

LOGGER = get_logger(__name__)


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

    def __init__(
        self,
        config: ADKConfig,
        provider: CalendarProvider,
        session_manager: SessionManager | None = None,
        context_tools: list | None = None,
    ) -> None:
        self.config = config
        self.provider = provider
        self.session_manager = session_manager
        self.system_instruction = system_instruction(
            "calendar agent. Call the calendar tool, classify events, and only surface redacted summaries."
        )
        self._llm_agent = genai_agent.LlmAgent(
            model=self.config.model,
            system_instruction=self.system_instruction,
            name="calendar-agent",
            tools=[provider.as_tool(), *(context_tools or [])],
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

    def get_schedule_profile(
        self,
        user_id: str,
        target_date: date,
        end_date: date | None = None,
        session_id: str | None = None,
    ) -> Dict[str, object]:
        """Fetch events and return schedule classification."""

        with operation_context("agent:calendar.get_schedule_profile", session_id=session_id) as correlation_id:
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

            if self.session_manager and session_id:
                self.session_manager.record_event(
                    session_id,
                    event_type="calendar_profile",
                    payload={
                        "date_range": {"start": target_date.isoformat(), "end": end.isoformat()},
                        "user_facing_summary": user_facing_summary,
                        "debug": debug_summary,
                    },
                )

            response = {
                "user_id": user_id,
                "date_range": {"start": target_date.isoformat(), "end": end.isoformat()},
                "events": safe_events,
                "day_parts": sorted(set(day_parts)),
                "formality": formality,
                "movement": movement,
                "user_facing_summary": user_facing_summary,
                "debug_summary": debug_summary,
            }

            log_event(
                LOGGER,
                level=logging.INFO,
                event="agent_call_completed",
                agent="calendar",
                method="get_schedule_profile",
                correlation_id=correlation_id,
                request={"user_id": user_id, "date": target_date.isoformat()},
                event_count=len(events),
                formality=formality,
            )
            return response


__all__ = ["CalendarAgent"]
