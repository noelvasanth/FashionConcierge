"""Calendar provider abstractions and implementations for Phase 4."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime
from typing import List

import google.auth
from google.auth.transport.requests import Request
import requests

from adk_app.genai_fallback import ensure_genai_imports

ensure_genai_imports()

from google.generativeai import agent as genai_agent
from tools.observability import instrument_tool


LOGGER = logging.getLogger(__name__)
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]


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
            func=instrument_tool("get_calendar_events")(self.get_events),
        )


class GoogleCalendarProvider(CalendarProvider):
    """Google Calendar provider with OAuth/ADC support and input validation."""

    def __init__(
        self,
        project_id: str,
        calendar_id: str | None = None,
        credentials_path: str | None = None,
        timeout_seconds: float = 5.0,
    ) -> None:
        if not project_id:
            raise ValueError("project_id is required for Google Calendar provider")
        self.project_id = project_id
        self.calendar_id = calendar_id or "primary"
        self.credentials_path = credentials_path
        self.timeout_seconds = timeout_seconds

    def _get_credentials(self):
        if self.credentials_path:
            credentials, _ = google.auth.load_credentials_from_file(
                self.credentials_path, scopes=SCOPES
            )
        else:
            credentials, _ = google.auth.default(scopes=SCOPES)

        if not credentials.valid:
            credentials.refresh(Request())

        return credentials

    def _parse_datetime(self, raw: str | None) -> datetime:
        if not raw:
            raise ValueError("Missing datetime value from calendar event")
        cleaned = raw.replace("Z", "+00:00")
        return datetime.fromisoformat(cleaned)

    def _coerce_event(self, payload: dict) -> CalendarEvent:
        start_info = payload.get("start", {})
        end_info = payload.get("end", {})
        is_all_day = "date" in start_info
        start_raw = start_info.get("dateTime") or start_info.get("date")
        end_raw = end_info.get("dateTime") or end_info.get("date")
        start_time = self._parse_datetime(start_raw)
        end_time = self._parse_datetime(end_raw)
        return CalendarEvent(
            title=payload.get("summary") or "Untitled event",
            start_time=start_time,
            end_time=end_time,
            description=payload.get("description"),
            location=payload.get("location"),
            is_all_day=is_all_day,
        )

    def get_events(self, user_id: str, start_date: date, end_date: date) -> List[CalendarEvent]:
        if not user_id:
            raise ValueError("user_id is required")
        if start_date > end_date:
            raise ValueError("start_date must be on or before end_date")

        LOGGER.info(
            "Fetching calendar events",
            extra={"user_id": user_id, "start_date": str(start_date), "end_date": str(end_date)},
        )

        try:
            credentials = self._get_credentials()
        except Exception as exc:  # pragma: no cover - defensive path
            LOGGER.error("Failed to acquire Google credentials", exc_info=exc)
            return []

        time_min = datetime.combine(start_date, datetime.min.time()).isoformat() + "Z"
        time_max = datetime.combine(end_date, datetime.max.time()).isoformat() + "Z"

        params = {
            "timeMin": time_min,
            "timeMax": time_max,
            "singleEvents": "true",
            "orderBy": "startTime",
            "maxResults": 50,
        }

        headers = {"Authorization": f"Bearer {credentials.token}"}
        url = f"https://www.googleapis.com/calendar/v3/calendars/{self.calendar_id}/events"

        try:
            response = requests.get(url, headers=headers, params=params, timeout=self.timeout_seconds)
            response.raise_for_status()
            payload = response.json()
            events: List[CalendarEvent] = []
            for item in payload.get("items", []):
                try:
                    events.append(self._coerce_event(item))
                except Exception as exc:  # pragma: no cover - defensive path
                    LOGGER.warning("Skipping malformed calendar event", exc_info=exc)
            return events
        except requests.Timeout:
            LOGGER.error("Google Calendar request timed out")
            return []
        except requests.RequestException as exc:  # pragma: no cover - defensive path
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
