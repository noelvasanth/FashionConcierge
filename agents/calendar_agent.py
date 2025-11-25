"""Calendar agent stub."""

from datetime import date
from typing import Dict, List

from google.generativeai import agent as genai_agent

from adk_app.config import ADKConfig
from tools.calendar import CalendarProvider


class CalendarAgent:
    """Classifies calendar events into schedule profiles."""

    def __init__(self, config: ADKConfig, provider: CalendarProvider) -> None:
        self.config = config
        self.provider = provider
        self.system_instruction = (
            "You fetch calendar events and summarize the day into a schedule "
            "profile with activities and formality levels."
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

    def get_schedule_profile(self, user_id: str, target_date: date) -> Dict[str, str]:
        """Fetch events via the provider and return a stub schedule profile."""

        events: List[Dict[str, str]] = self.provider.get_events(user_id=user_id, date_range=[target_date])
        return {
            "user_id": user_id,
            "date": target_date.isoformat(),
            "events": events,
            "profile": "office-day",
        }
