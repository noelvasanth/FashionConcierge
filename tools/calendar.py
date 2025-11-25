"""Calendar provider abstractions and tools."""

from abc import ABC, abstractmethod
from datetime import date
from typing import Dict, Iterable, List

from adk_app.genai_fallback import ensure_genai_imports

ensure_genai_imports()

from google.generativeai import agent as genai_agent


class CalendarProvider(ABC):
    """Abstract calendar provider interface."""

    @abstractmethod
    def get_events(self, user_id: str, date_range: Iterable[date]) -> List[Dict[str, str]]:
        """Fetch events for the user and date range."""

    def as_tool(self) -> genai_agent.Tool:
        """Wrap the provider in an ADK tool."""

        return genai_agent.Tool(
            name="get_calendar_events",
            description="Fetch calendar events for the user and date range.",
            func=self.get_events,
        )


class GoogleCalendarProvider(CalendarProvider):
    """Placeholder Google Calendar provider."""

    def __init__(self, project_id: str) -> None:
        self.project_id = project_id

    def get_events(self, user_id: str, date_range: Iterable[date]) -> List[Dict[str, str]]:
        # Real implementation will call Google Calendar API.
        return [
            {
                "user_id": user_id,
                "date": next(iter(date_range)).isoformat(),
                "summary": "Sample calendar event",
                "type": "meeting",
            }
        ]
