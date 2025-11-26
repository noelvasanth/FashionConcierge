"""Calendar provider abstractions and implementations for Phase 4."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime
from typing import List

from adk_app.genai_fallback import ensure_genai_imports

ensure_genai_imports()

from google.generativeai import agent as genai_agent


LOGGER = logging.getLogger(__name__)


@dataclass
class CalendarEvent:
    """Minimal calendar event payload safe for logs and memory."""

    title: str
    start_time: datetime
    end_time: datetime
    description: str | None = None
    location: str | None = None
    is_all_day: bool = False


class CalendarProvider(ABC):
    """Abstract calendar provider interface."""

    @abstractmethod
    def get_events(self, user_id: str, start_date: date, end_date: date) -> List[CalendarEvent]:
        """Fetch calendar events for the user in the inclusive date range."""

    def as_tool(self) -> genai_agent.Tool:
        """Expose provider as an ADK function tool."""

        return genai_agent.Tool(
            name="get_calendar_events",
            description="Fetch calendar events for a user and date range.",
            func=self.get_events,
        )


class GoogleCalendarProvider(CalendarProvider):
    """Google Calendar provider placeholder with safe fallbacks."""

    def __init__(self, project_id: str, timeout_seconds: float = 5.0) -> None:
        self.project_id = project_id
        self.timeout_seconds = timeout_seconds

    def get_events(self, user_id: str, start_date: date, end_date: date) -> List[CalendarEvent]:
        try:
            LOGGER.info(
                "Fetching calendar events", extra={"user_id": user_id, "start_date": str(start_date), "end_date": str(end_date)}
            )
            # Placeholder deterministic fallback. Real implementation would call Google Calendar API with tight timeouts.
            start_dt = datetime.combine(start_date, datetime.min.time())
            end_dt = datetime.combine(start_date, datetime.min.time()).replace(hour=9)
            return [
                CalendarEvent(
                    title="Team sync",
                    start_time=start_dt.replace(hour=9),
                    end_time=end_dt.replace(hour=10),
                    description=None,
                    location=None,
                    is_all_day=False,
                )
            ]
        except Exception as exc:  # pragma: no cover - defensive path
            LOGGER.error("Calendar API unreachable", exc_info=exc)
            return []


class MockCalendarProvider(CalendarProvider):
    """Offline deterministic calendar provider for tests."""

    def __init__(self, events: List[CalendarEvent] | None = None) -> None:
        self._events = events or []

    def get_events(self, user_id: str, start_date: date, end_date: date) -> List[CalendarEvent]:
        LOGGER.info(
            "Returning mock calendar events", extra={"user_id": user_id, "start_date": str(start_date), "end_date": str(end_date)}
        )
        return list(self._events)


__all__ = ["CalendarEvent", "CalendarProvider", "GoogleCalendarProvider", "MockCalendarProvider"]
