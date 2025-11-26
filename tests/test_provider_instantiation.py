from datetime import date

from adk_app.genai_fallback import ensure_genai_imports

ensure_genai_imports()
from google.generativeai import agent as genai_agent  # noqa: E402

from tools import calendar as legacy_calendar  # noqa: E402
from tools import weather as legacy_weather  # noqa: E402
from tools.calendar_provider import CalendarProvider, GoogleCalendarProvider, MockCalendarProvider  # noqa: E402
from tools.weather_provider import MockWeatherProvider, OpenWeatherProvider, WeatherProvider  # noqa: E402


def test_google_calendar_provider_tool_registration() -> None:
    provider = GoogleCalendarProvider(project_id="demo-project")
    tool = provider.as_tool()
    assert isinstance(tool, genai_agent.Tool)
    assert isinstance(provider, CalendarProvider)


def test_openweather_provider_fallback_and_tool() -> None:
    provider = OpenWeatherProvider()
    profile = provider.get_forecast("Paris", date(2024, 1, 1))
    assert profile.clothing_guidance
    assert isinstance(provider.as_tool(), genai_agent.Tool)
    assert isinstance(provider, WeatherProvider)


def test_mock_providers_and_shims() -> None:
    calendar_mock = MockCalendarProvider()
    weather_mock = MockWeatherProvider()

    assert isinstance(calendar_mock, CalendarProvider)
    assert isinstance(weather_mock, WeatherProvider)

    # Legacy shims should re-export canonical classes
    assert legacy_calendar.GoogleCalendarProvider is GoogleCalendarProvider
    assert legacy_weather.OpenWeatherProvider is OpenWeatherProvider
