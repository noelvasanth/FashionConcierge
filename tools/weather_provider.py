"""Weather provider abstractions and implementations for Phase 4."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date

from adk_app.genai_fallback import ensure_genai_imports

ensure_genai_imports()

from google.generativeai import agent as genai_agent


LOGGER = logging.getLogger(__name__)


@dataclass
class WeatherProfile:
    """Minimal weather profile."""

    temp_min: float
    temp_max: float
    precipitation_probability: float
    wind_speed: float
    weather_condition: str
    clothing_guidance: str


class WeatherProvider(ABC):
    """Abstract weather provider interface."""

    @abstractmethod
    def get_forecast(self, location: str, date: date) -> WeatherProfile:
        """Return a weather forecast payload."""

    def as_tool(self) -> genai_agent.Tool:
        return genai_agent.Tool(
            name="get_weather_forecast",
            description="Get weather forecast for a location and date.",
            func=self.get_forecast,
        )


class OpenWeatherProvider(WeatherProvider):
    """Simple placeholder provider with robust logging and fallbacks."""

    def __init__(self, api_key: str | None = None, timeout_seconds: float = 5.0) -> None:
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    def get_forecast(self, location: str, date: date) -> WeatherProfile:
        try:
            LOGGER.info("Fetching weather forecast", extra={"location": location, "date": str(date)})
            # Deterministic fallback forecast; real implementation would call an API.
            return WeatherProfile(
                temp_min=8.0,
                temp_max=15.0,
                precipitation_probability=0.2,
                wind_speed=12.0,
                weather_condition="cloudy",
                clothing_guidance="Light jacket recommended",
            )
        except Exception as exc:  # pragma: no cover - defensive path
            LOGGER.error("Weather API unreachable", exc_info=exc)
            return WeatherProfile(
                temp_min=0.0,
                temp_max=0.0,
                precipitation_probability=0.0,
                wind_speed=0.0,
                weather_condition="unknown",
                clothing_guidance="No forecast available",
            )


class MockWeatherProvider(WeatherProvider):
    """Offline deterministic weather provider for tests."""

    def __init__(self, profile: WeatherProfile | None = None) -> None:
        self.profile = profile or WeatherProfile(
            temp_min=12.0,
            temp_max=18.0,
            precipitation_probability=0.1,
            wind_speed=5.0,
            weather_condition="clear",
            clothing_guidance="T-shirt weather",
        )

    def get_forecast(self, location: str, date: date) -> WeatherProfile:
        LOGGER.info("Returning mock forecast", extra={"location": location, "date": str(date)})
        return self.profile


__all__ = ["WeatherProfile", "WeatherProvider", "OpenWeatherProvider", "MockWeatherProvider"]
