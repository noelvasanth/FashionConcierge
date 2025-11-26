"""Phase 5 tests for context-aware styling, scoring and orchestration."""

from __future__ import annotations

from datetime import datetime, date
from pathlib import Path
from typing import List

import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from adk_app.config import ADKConfig
from agents.calendar_agent import CalendarAgent
from agents.orchestrator import OrchestratorAgent
from agents.outfit_stylist_agent import OutfitStylistAgent
from agents.weather_agent import WeatherAgent
from logic.contextual_filtering import (
    filter_by_formality,
    filter_by_mood,
    filter_by_movement,
    filter_by_weather,
)
from logic.outfit_scoring import calculate_color_harmony_metrics, score_outfit
from models.mood_styles import get_mood_style
from models.wardrobe_item import WardrobeItem
from tools.calendar_provider import CalendarEvent, MockCalendarProvider
from tools.weather_provider import MockWeatherProvider, WeatherProfile
from tools.wardrobe_store import SQLiteWardrobeStore
from tools.wardrobe_tools import WardrobeTools


def _build_items(user_id: str = "demo") -> List[WardrobeItem]:
    return [
        WardrobeItem(
            item_id="top1",
            user_id=user_id,
            image_url="http://example.com/t1.jpg",
            source_url="http://example.com/t1",
            category="top",
            sub_category="shirt",
            colors=["blue"],
            materials=["cotton"],
            style_tags=["business", "smart"],
            season_tags=["all_year"],
        ),
        WardrobeItem(
            item_id="bottom1",
            user_id=user_id,
            image_url="http://example.com/b1.jpg",
            source_url="http://example.com/b1",
            category="bottom",
            sub_category="trousers",
            colors=["black"],
            materials=["wool"],
            style_tags=["business"],
            season_tags=["all_year"],
        ),
        WardrobeItem(
            item_id="shoes1",
            user_id=user_id,
            image_url="http://example.com/s1.jpg",
            source_url="http://example.com/s1",
            category="shoes",
            sub_category="sneakers",
            colors=["white"],
            materials=["leather"],
            style_tags=["casual", "business"],
            season_tags=["all_year"],
        ),
        WardrobeItem(
            item_id="shoes2",
            user_id=user_id,
            image_url="http://example.com/s2.jpg",
            source_url="http://example.com/s2",
            category="shoes",
            sub_category="heels",
            colors=["black"],
            materials=["suede"],
            style_tags=["business"],
            season_tags=["all_year"],
        ),
        WardrobeItem(
            item_id="outer1",
            user_id=user_id,
            image_url="http://example.com/o1.jpg",
            source_url="http://example.com/o1",
            category="outerwear",
            sub_category="coat",
            colors=["gray"],
            materials=["wool"],
            style_tags=["business"],
            season_tags=["cold_weather"],
        ),
    ]


def test_filtering_weather_and_formality(tmp_path):
    weather_profile = {
        "temperature_range": "cold",
        "layers_required": "two",
        "rain_sensitivity": "heavy rain",
        "raw_forecast": WeatherProfile(0, 2, 0.8, 5.0, "rain", ""),
    }
    schedule_profile = {"formality": "business", "movement": "low", "day_parts": []}
    items = _build_items()

    weather_result = filter_by_weather(items, weather_profile)
    assert "shoes2" in weather_result.removed
    formality_result = filter_by_formality(weather_result.items, schedule_profile)
    assert formality_result.removed or weather_result.removed
    movement_result = filter_by_movement(formality_result.items, schedule_profile)
    assert movement_result.debug["movement"] == "low"


def test_filtering_mood_overlap():
    items = _build_items()
    mood_result = filter_by_mood(items, "business")
    assert len(mood_result.items) > 0
    profile_tags = set(get_mood_style("business").style_tags)
    assert all(set(item.style_tags).intersection(profile_tags) for item in mood_result.items)


def test_scoring_monotonicity():
    items = _build_items()
    warm_context = {"movement_requirement": "low", "warmth_requirement": "high", "formality_requirement": "business"}
    color_metrics = calculate_color_harmony_metrics(items[:3])
    score_without_outer = score_outfit(items[:3], warm_context, get_mood_style("business"), color_metrics)
    score_with_outer = score_outfit(items[:4], warm_context, get_mood_style("business"), color_metrics)
    assert 0 <= score_with_outer["composite_score"] <= 1
    assert score_with_outer["composite_score"] >= score_without_outer["composite_score"]


def test_stylist_agent_ranking(tmp_path):
    store = SQLiteWardrobeStore(tmp_path / "wardrobe.db")
    for item in _build_items("agent"):
        store.create_item(item)
    tools = WardrobeTools(store)
    config = ADKConfig.from_env()
    stylist = OutfitStylistAgent(config, tools)

    schedule_profile = {"formality": "business", "movement": "high", "day_parts": ["office"]}
    weather_profile = {"temperature_range": "cold", "layers_required": "two"}
    daily_context = {"formality_requirement": "business", "movement_requirement": "high", "warmth_requirement": "high"}

    response = stylist.recommend_outfit(
        user_id="agent",
        mood="business",
        schedule_profile=schedule_profile,
        weather_profile=weather_profile,
        daily_context=daily_context,
        top_n=2,
    )
    assert response["ranked_outfits"]
    assert response["ranked_outfits"][0]["composite_score"] >= response["ranked_outfits"][-1]["composite_score"]
    debug = response["debug_summary"]
    assert debug["candidate_outfits"] >= 1
    assert debug["filters"]["final_count"] >= 1


def test_orchestrator_end_to_end(tmp_path):
    store = SQLiteWardrobeStore(tmp_path / "wardrobe.db")
    for item in _build_items("orch"):
        store.create_item(item)
    wardrobe_tools = WardrobeTools(store)

    config = ADKConfig.from_env()
    calendar_provider = MockCalendarProvider(
        [
            CalendarEvent(
                title="Team sync",
                start_time=datetime(2025, 11, 30, 9, 0),
                end_time=datetime(2025, 11, 30, 10, 0),
            )
        ]
    )
    weather_provider = MockWeatherProvider(
        WeatherProfile(temp_min=2, temp_max=6, precipitation_probability=0.2, wind_speed=5, weather_condition="cloudy", clothing_guidance="")
    )

    calendar_agent = CalendarAgent(config, calendar_provider)
    weather_agent = WeatherAgent(config, weather_provider)
    stylist_agent = OutfitStylistAgent(config, wardrobe_tools)
    orchestrator = OrchestratorAgent(
        config,
        tools=[],
        stylist_agent=stylist_agent,
        calendar_agent=calendar_agent,
        weather_agent=weather_agent,
    )

    response = orchestrator.plan_outfit(user_id="orch", date=date(2025, 11, 30), location="Amsterdam", mood="business")
    assert response["status"] == "ok"
    assert response["top_outfits"]
    assert response["context"]["formality_requirement"] == "business"
    assert "debug_summary" in response

