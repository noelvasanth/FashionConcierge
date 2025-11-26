"""Weather agent that maps forecasts into clothing-friendly labels."""

from __future__ import annotations

import logging
from datetime import date
from typing import Dict

from adk_app.genai_fallback import ensure_genai_imports

ensure_genai_imports()

from google.generativeai import agent as genai_agent

from adk_app.config import ADKConfig
from adk_app.logging_config import get_logger, log_event, operation_context
from tools.weather_provider import WeatherProfile, WeatherProvider
from memory.session_store import SessionManager


LOGGER = get_logger(__name__)


class WeatherAgent:
    """Fetches weather and classifies wardrobe-relevant signals."""

    def __init__(
        self,
        config: ADKConfig,
        provider: WeatherProvider,
        session_manager: SessionManager | None = None,
        context_tools: list | None = None,
    ) -> None:
        self.config = config
        self.provider = provider
        self.session_manager = session_manager
        self.system_instruction = (
            "Call the weather tool, translate forecasts into clothing needs, and explain thresholds."
        )
        self._llm_agent = genai_agent.LlmAgent(
            model=self.config.model,
            system_instruction=self.system_instruction,
            name="weather-agent",
            tools=[provider.as_tool(), *(context_tools or [])],
        )

    @property
    def adk_agent(self) -> genai_agent.LlmAgent:
        return self._llm_agent

    def _temperature_range(self, profile: WeatherProfile) -> str:
        avg_temp = (profile.temp_min + profile.temp_max) / 2
        if avg_temp < 5:
            return "cold"
        if avg_temp < 12:
            return "cool"
        if avg_temp < 18:
            return "mild"
        if avg_temp < 24:
            return "warm"
        return "hot"

    def _layers_required(self, temp_range: str) -> str:
        return {
            "cold": "two plus",
            "cool": "two",
            "mild": "one",
            "warm": "zero",
            "hot": "zero",
        }[temp_range]

    def _rain_sensitivity(self, precipitation_probability: float) -> str:
        if precipitation_probability > 0.6:
            return "heavy rain"
        if precipitation_probability > 0.3:
            return "light rain"
        return "dry"

    def get_weather_profile(
        self, user_id: str, location: str, target_date: date, session_id: str | None = None
    ) -> Dict[str, object]:
        """Fetch forecast and return deterministic clothing labels."""

        with operation_context("agent:weather.get_weather_profile", session_id=session_id) as correlation_id:
            forecast = self.provider.get_forecast(location=location, date=target_date)
            temp_range = self._temperature_range(forecast)
            layers = self._layers_required(temp_range)
            rain = self._rain_sensitivity(forecast.precipitation_probability)
            debug_summary = {
                "input_assumptions": {
                    "location": location,
                    "date": target_date.isoformat(),
                },
                "thresholds": {
                    "temperature_bands_c": {"cold": "<5", "cool": "<12", "mild": "<18", "warm": "<24", "hot": ">=24"},
                    "rain_prob_thresholds": {"heavy": ">0.6", "light": ">0.3"},
                },
                "classification_rationale": {
                    "temperature_range": temp_range,
                    "layers_required": layers,
                    "rain_sensitivity": rain,
                },
            }

            user_facing_summary = (
                f"Forecast {forecast.weather_condition} with {forecast.temp_min:.0f}-{forecast.temp_max:.0f}°C. "
                f"Feels {temp_range}; layers {layers}; rain risk {rain}."
            )

            if self.session_manager and session_id:
                self.session_manager.record_event(
                    session_id,
                    event_type="weather_profile",
                    payload={
                        "location": location,
                        "date": target_date.isoformat(),
                        "user_facing_summary": user_facing_summary,
                        "debug": debug_summary,
                    },
                )

            response = {
                "user_id": user_id,
                "location": location,
                "date": target_date.isoformat(),
                "raw_forecast": forecast,
                "temperature_range": temp_range,
                "layers_required": layers,
                "rain_sensitivity": rain,
                "user_facing_summary": user_facing_summary,
                "debug_summary": debug_summary,
            }

            log_event(
                LOGGER,
                level=logging.INFO,
                event="agent_call_completed",
                agent="weather",
                method="get_weather_profile",
                correlation_id=correlation_id,
                location=location,
                date=target_date.isoformat(),
                rain=rain,
                temp_range=temp_range,
            )
            return response


__all__ = ["WeatherAgent"]
