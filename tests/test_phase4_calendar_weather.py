"""Phase 4 calendar, weather, and context synthesis coverage."""

from datetime import date, datetime

from adk_app.config import ADKConfig
from agents.calendar_agent import CalendarAgent
from agents.orchestrator import OrchestratorAgent
from agents.weather_agent import WeatherAgent
from logic.context_synthesizer import synthesize_context
from tools.calendar_provider import CalendarEvent, MockCalendarProvider
from tools.weather_provider import MockWeatherProvider, WeatherProfile


def _demo_config() -> ADKConfig:
    return ADKConfig(project_id="test-project", api_key="dummy-key")


def test_calendar_agent_classifies_events_and_summarizes() -> None:
    target = date(2025, 11, 30)
    events = [
        CalendarEvent(
            title="Team meeting with leadership",
            start_time=datetime.combine(target, datetime.min.time()).replace(hour=10),
            end_time=datetime.combine(target, datetime.min.time()).replace(hour=11),
        ),
        CalendarEvent(
            title="Gym session",
            start_time=datetime.combine(target, datetime.min.time()).replace(hour=7),
            end_time=datetime.combine(target, datetime.min.time()).replace(hour=8),
        ),
        CalendarEvent(
            title="Dinner with friends downtown",
            start_time=datetime.combine(target, datetime.min.time()).replace(hour=19),
            end_time=datetime.combine(target, datetime.min.time()).replace(hour=20),
        ),
    ]
    provider = MockCalendarProvider(events)
    agent = CalendarAgent(config=_demo_config(), provider=provider)

    profile = agent.get_schedule_profile(user_id="demo", target_date=target)

    assert profile["formality"] == "business"
    assert profile["movement"] == "high"
    assert "dinner" in profile["day_parts"]
    assert profile["debug_summary"]["number_of_events"] == 3
    for event in profile["events"]:
        assert len(event["title"]) <= 23  # truncated for privacy


def test_weather_agent_maps_forecast_to_labels_and_debug() -> None:
    provider = MockWeatherProvider(
        WeatherProfile(
            temp_min=2.0,
            temp_max=6.0,
            precipitation_probability=0.7,
            wind_speed=20.0,
            weather_condition="rain",
            clothing_guidance="Heavy coat and boots",
        )
    )
    agent = WeatherAgent(config=_demo_config(), provider=provider)

    weather = agent.get_weather_profile(user_id="demo", location="Amsterdam", target_date=date.today())

    assert weather["temperature_range"] == "cold"
    assert weather["layers_required"] == "two plus"
    assert weather["rain_sensitivity"] == "heavy rain"
    assert "temperature_bands_c" in weather["debug_summary"]["thresholds"]


def test_context_synthesizer_combines_schedule_and_weather() -> None:
    schedule_profile = {
        "formality": "business",
        "movement": "high",
        "day_parts": ["office block", "dinner"],
    }
    weather_profile = {
        "temperature_range": "cool",
        "rain_sensitivity": "light rain",
        "raw_forecast": WeatherProfile(
            temp_min=8.0,
            temp_max=12.0,
            precipitation_probability=0.4,
            wind_speed=5.0,
            weather_condition="cloudy",
            clothing_guidance="Light layers",
        ),
    }

    context = synthesize_context(schedule_profile, weather_profile)

    assert context["formality_requirement"] == "business"
    assert context["warmth_requirement"] == "medium"
    assert context["weather_risk_level"] == "medium"
    assert "combined_rules_applied" in context["debug_summary"]


def test_orchestrator_returns_daily_context() -> None:
    target = date(2025, 11, 30)
    events = [
        CalendarEvent(
            title="Project work",
            start_time=datetime.combine(target, datetime.min.time()).replace(hour=9),
            end_time=datetime.combine(target, datetime.min.time()).replace(hour=12),
        )
    ]
    calendar_agent = CalendarAgent(config=_demo_config(), provider=MockCalendarProvider(events))
    weather_agent = WeatherAgent(
        config=_demo_config(),
        provider=MockWeatherProvider(
            WeatherProfile(
                temp_min=15.0,
                temp_max=18.0,
                precipitation_probability=0.05,
                wind_speed=3.0,
                weather_condition="clear",
                clothing_guidance="Light jacket",
            )
        ),
    )
    orchestrator = OrchestratorAgent(
        config=_demo_config(), tools=[], stylist_agent=None, calendar_agent=calendar_agent, weather_agent=weather_agent
    )

    response = orchestrator.plan_outfit_context(
        user_id="demo", target_date=target.isoformat(), location="Amsterdam", mood="trendy"
    )

    assert response["status"] == "ok"
    assert "daily_context" in response
    assert response["daily_context"]["formality_requirement"] == "business"
    assert response["schedule_profile"]["debug_summary"]["number_of_events"] == 1
