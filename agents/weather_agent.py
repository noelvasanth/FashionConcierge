"""Weather agent stub."""

from datetime import date
from typing import Dict

from google.generativeai import agent as genai_agent

from adk_app.config import ADKConfig
from tools.weather import WeatherProvider


class WeatherAgent:
    """Wraps a weather provider and summarizes clothing guidance."""

    def __init__(self, config: ADKConfig, provider: WeatherProvider) -> None:
        self.config = config
        self.provider = provider
        self.system_instruction = (
            "You call the weather tool to fetch forecasts and return clothing guidance "
            "including layers and rain readiness."
        )
        self._llm_agent = genai_agent.LlmAgent(
            model=self.config.model,
            system_instruction=self.system_instruction,
            name="weather-agent",
            tools=[provider.as_tool()],
        )

    @property
    def adk_agent(self) -> genai_agent.LlmAgent:
        return self._llm_agent

    def get_weather_profile(self, location: str, target_date: date) -> Dict[str, str]:
        """Return a simple weather profile using the provider."""

        forecast = self.provider.get_forecast(location=location, date=target_date)
        return {
            "location": location,
            "date": target_date.isoformat(),
            "forecast": forecast,
            "profile": "mild-day",
        }
