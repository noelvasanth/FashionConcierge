"""Weather provider abstractions and implementations for Phase 4."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from typing import List

import requests
from pydantic import BaseModel, ValidationError

from adk_app.genai_fallback import ensure_genai_imports

ensure_genai_imports()

from google.generativeai import agent as genai_agent
from tools.observability import instrument_tool


LOGGER = logging.getLogger(__name__)


class _WeatherCondition(BaseModel):
    description: str = "unknown"


class _Wind(BaseModel):
    speed: float = 0.0


class _Main(BaseModel):
    temp_min: float
    temp_max: float


class _ForecastEntry(BaseModel):
    dt_txt: str
    main: _Main
    pop: float = 0.0
    wind: _Wind
    weather: List[_WeatherCondition] = []


class _ForecastResponse(BaseModel):
    list: List[_ForecastEntry] = []


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
            func=instrument_tool("get_weather_forecast")(self.get_forecast),
        )


class OpenWeatherProvider(WeatherProvider):
    """OpenWeather provider with schema validation and graceful fallbacks."""

    def __init__(self, api_key: str | None = None, timeout_seconds: float = 5.0, units: str = "metric") -> None:
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds
        self.units = units

    def _fallback_profile(self, reason: str) -> WeatherProfile:
        LOGGER.warning("Using fallback weather profile", extra={"reason": reason})
        return WeatherProfile(
            temp_min=12.0,
            temp_max=18.0,
            precipitation_probability=0.1,
            wind_speed=5.0,
            weather_condition="unknown",
            clothing_guidance="Light layers recommended",
        )

    def _guidance(self, temp_min: float, temp_max: float, precip: float) -> str:
        avg_temp = (temp_min + temp_max) / 2
        needs_layers = avg_temp < 15
        rain_risk = precip > 0.3
        if rain_risk and needs_layers:
            return "Carry a rain jacket and warm layers"
        if rain_risk:
            return "Pack a light rain layer"
        if needs_layers:
            return "Light jacket recommended"
        return "T-shirt friendly weather"

    def _choose_entry(self, entries: List["_ForecastEntry"], target_date: date) -> "_ForecastEntry | None":
        target_day = target_date.isoformat()
        for entry in entries:
            if entry.dt_txt.startswith(target_day):
                return entry
        return entries[0] if entries else None

    def get_forecast(self, location: str, date: date) -> WeatherProfile:
        if not location:
            raise ValueError("location is required for weather lookups")

        if not self.api_key:
            return self._fallback_profile("missing_api_key")

        LOGGER.info("Fetching weather forecast", extra={"location": location, "date": str(date)})
        params = {
            "q": location,
            "appid": self.api_key,
            "units": self.units,
        }
        url = "https://api.openweathermap.org/data/2.5/forecast"

        try:
            response = requests.get(url, params=params, timeout=self.timeout_seconds)
            response.raise_for_status()
            payload = response.json()
            parsed = _ForecastResponse.model_validate(payload)
            entry = self._choose_entry(parsed.list, date)
            if not entry:
                return self._fallback_profile("no_forecast_entries")

            temp_min = entry.main.temp_min
            temp_max = entry.main.temp_max
            precipitation = entry.pop
            condition = entry.weather[0].description if entry.weather else "unknown"
            guidance = self._guidance(temp_min, temp_max, precipitation)
            return WeatherProfile(
                temp_min=temp_min,
                temp_max=temp_max,
                precipitation_probability=precipitation,
                wind_speed=entry.wind.speed,
                weather_condition=condition,
                clothing_guidance=guidance,
            )
        except (requests.Timeout, requests.RequestException) as exc:
            LOGGER.error("Weather API unreachable", exc_info=exc)
            return self._fallback_profile("request_error")
        except ValidationError as exc:
            LOGGER.error("Weather payload schema validation failed", exc_info=exc)
            return self._fallback_profile("schema_validation")


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
