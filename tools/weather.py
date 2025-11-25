"""Weather provider abstractions and tools."""

from abc import ABC, abstractmethod
from datetime import date
from typing import Dict

from google.generativeai import agent as genai_agent


class WeatherProvider(ABC):
    """Abstract weather provider interface."""

    @abstractmethod
    def get_forecast(self, location: str, date: date) -> Dict[str, str]:
        """Return a weather forecast payload."""

    def as_tool(self) -> genai_agent.Tool:
        return genai_agent.Tool(
            name="get_weather_forecast",
            description="Get weather forecast for a location and date.",
            func=self.get_forecast,
        )


class OpenWeatherProvider(WeatherProvider):
    """Simple placeholder provider."""

    def get_forecast(self, location: str, date: date) -> Dict[str, str]:
        return {
            "location": location,
            "date": date.isoformat(),
            "min_temp_c": 12,
            "max_temp_c": 18,
            "rain_chance": 0.15,
        }
