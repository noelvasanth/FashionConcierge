"""Evaluation scenarios exercising moods, weather, and calendar patterns."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Dict, List

from tools.calendar_provider import CalendarEvent
from tools.weather_provider import WeatherProfile


@dataclass
class EvaluationScenario:
    name: str
    description: str
    mood: str
    location: str
    target_date: date
    weather_profile: WeatherProfile
    calendar_events: List[CalendarEvent]
    wardrobe_items: List[Dict[str, object]]
    expectations: Dict[str, object]


def _event(title: str, day: date, hour: int) -> CalendarEvent:
    start = datetime.combine(day, datetime.min.time()) + timedelta(hours=hour)
    end = start + timedelta(hours=1)
    return CalendarEvent(title=title, start_time=start, end_time=end, is_all_day=False)


def _wardrobe_fixtures() -> List[Dict[str, object]]:
    return [
        {
            "item_id": "top_blazer",
            "image_url": "https://example.com/blazer.jpg",
            "source_url": "https://example.com/blazer",
            "category": "top",
            "sub_category": "blazer",
            "colors": ["navy"],
            "style_tags": ["business", "casual"],
            "season_tags": ["all_year"],
        },
        {
            "item_id": "top_tee",
            "image_url": "https://example.com/tee.jpg",
            "source_url": "https://example.com/tee",
            "category": "top",
            "sub_category": "tee",
            "colors": ["white"],
            "style_tags": ["casual"],
            "season_tags": ["warm_weather"],
        },
        {
            "item_id": "top_sweater",
            "image_url": "https://example.com/sweater.jpg",
            "source_url": "https://example.com/sweater",
            "category": "top",
            "sub_category": "sweater",
            "colors": ["gray"],
            "style_tags": ["casual"],
            "season_tags": ["cold_weather"],
        },
        {
            "item_id": "top_party_shirt",
            "image_url": "https://example.com/party-shirt.jpg",
            "source_url": "https://example.com/party-shirt",
            "category": "top",
            "sub_category": "shirt",
            "colors": ["red"],
            "style_tags": ["party", "festive"],
            "season_tags": ["all_year"],
        },
        {
            "item_id": "bottom_jeans",
            "image_url": "https://example.com/jeans.jpg",
            "source_url": "https://example.com/jeans",
            "category": "bottom",
            "sub_category": "jeans",
            "colors": ["blue"],
            "style_tags": ["casual"],
            "season_tags": ["all_year"],
        },
        {
            "item_id": "bottom_chinos",
            "image_url": "https://example.com/chinos.jpg",
            "source_url": "https://example.com/chinos",
            "category": "bottom",
            "sub_category": "chinos",
            "colors": ["beige"],
            "style_tags": ["business", "casual"],
            "season_tags": ["all_year"],
        },
        {
            "item_id": "bottom_party_trousers",
            "image_url": "https://example.com/party-trousers.jpg",
            "source_url": "https://example.com/party-trousers",
            "category": "bottom",
            "sub_category": "trousers",
            "colors": ["black"],
            "style_tags": ["party", "festive"],
            "season_tags": ["all_year"],
        },
        {
            "item_id": "shoes_sneakers",
            "image_url": "https://example.com/sneakers.jpg",
            "source_url": "https://example.com/sneakers",
            "category": "shoes",
            "sub_category": "sneakers",
            "colors": ["white"],
            "style_tags": ["casual", "sporty"],
            "season_tags": ["all_year"],
        },
        {
            "item_id": "shoes_heels",
            "image_url": "https://example.com/heels.jpg",
            "source_url": "https://example.com/heels",
            "category": "shoes",
            "sub_category": "heels",
            "colors": ["gold"],
            "style_tags": ["party", "festive"],
            "season_tags": ["all_year"],
        },
        {
            "item_id": "shoes_boots",
            "image_url": "https://example.com/boots.jpg",
            "source_url": "https://example.com/boots",
            "category": "shoes",
            "sub_category": "boots",
            "colors": ["black"],
            "style_tags": ["business", "street", "casual"],
            "season_tags": ["cold_weather"],
        },
        {
            "item_id": "outer_trench",
            "image_url": "https://example.com/trench.jpg",
            "source_url": "https://example.com/trench",
            "category": "outerwear",
            "sub_category": "trench",
            "colors": ["beige"],
            "style_tags": ["business"],
            "season_tags": ["all_year"],
        },
        {
            "item_id": "outer_puffer",
            "image_url": "https://example.com/puffer.jpg",
            "source_url": "https://example.com/puffer",
            "category": "outerwear",
            "sub_category": "puffer",
            "colors": ["black"],
            "style_tags": ["street", "business"],
            "season_tags": ["cold_weather"],
        },
        {
            "item_id": "accessory_scarf",
            "image_url": "https://example.com/scarf.jpg",
            "source_url": "https://example.com/scarf",
            "category": "accessory",
            "sub_category": "scarf",
            "colors": ["red"],
            "style_tags": ["festive", "casual"],
            "season_tags": ["cold_weather"],
        },
    ]


SCENARIOS = [
    EvaluationScenario(
        name="sunny_commute",
        description="Office commute on a mild, sunny day with casual mood.",
        mood="casual",
        location="San Francisco",
        target_date=date(2024, 6, 3),
        weather_profile=WeatherProfile(
            temp_min=12.0,
            temp_max=20.0,
            precipitation_probability=0.05,
            wind_speed=5.0,
            weather_condition="clear",
            clothing_guidance="Light layers",
        ),
        calendar_events=[
            _event("Commute", date(2024, 6, 3), 8),
            _event("Team sync", date(2024, 6, 3), 10),
            _event("Lunch", date(2024, 6, 3), 12),
        ],
        wardrobe_items=_wardrobe_fixtures(),
        expectations={"min_outfits": 1, "allow_casual": True},
    ),
    EvaluationScenario(
        name="rainy_office",
        description="Business casual office day with steady rain requiring outerwear.",
        mood="neutral",
        location="Seattle",
        target_date=date(2024, 10, 2),
        weather_profile=WeatherProfile(
            temp_min=8.0,
            temp_max=13.0,
            precipitation_probability=0.72,
            wind_speed=12.0,
            weather_condition="rain",
            clothing_guidance="Carry a rain jacket",
        ),
        calendar_events=[
            _event("Client meeting", date(2024, 10, 2), 9),
            _event("Office work", date(2024, 10, 2), 11),
        ],
        wardrobe_items=_wardrobe_fixtures(),
        expectations={"min_outfits": 1, "requires_outerwear": True},
    ),
    EvaluationScenario(
        name="festive_evening",
        description="Evening social plans with festive mood on warm night.",
        mood="festive",
        location="Austin",
        target_date=date(2024, 12, 20),
        weather_profile=WeatherProfile(
            temp_min=18.0,
            temp_max=26.0,
            precipitation_probability=0.1,
            wind_speed=6.0,
            weather_condition="clear",
            clothing_guidance="Light layers",
        ),
        calendar_events=[_event("Holiday party", date(2024, 12, 20), 19)],
        wardrobe_items=_wardrobe_fixtures(),
        expectations={"min_outfits": 1},
    ),
    EvaluationScenario(
        name="urban_travel",
        description="High-movement travel day with urban mood and medium rain risk.",
        mood="urban",
        location="New York",
        target_date=date(2024, 5, 18),
        weather_profile=WeatherProfile(
            temp_min=15.0,
            temp_max=22.0,
            precipitation_probability=0.35,
            wind_speed=14.0,
            weather_condition="cloudy",
            clothing_guidance="Pack a light layer",
        ),
        calendar_events=[
            _event("Airport commute", date(2024, 5, 18), 7),
            _event("Flight", date(2024, 5, 18), 9),
            _event("Hotel check-in", date(2024, 5, 18), 16),
        ],
        wardrobe_items=_wardrobe_fixtures(),
        expectations={"min_outfits": 1, "favor_movement": True},
    ),
    EvaluationScenario(
        name="winter_gym",
        description="Cold winter day with early workout and need for warmth.",
        mood="happy",
        location="Chicago",
        target_date=date(2024, 1, 10),
        weather_profile=WeatherProfile(
            temp_min=-2.0,
            temp_max=4.0,
            precipitation_probability=0.25,
            wind_speed=10.0,
            weather_condition="snow",
            clothing_guidance="Bundle up",
        ),
        calendar_events=[
            _event("Morning gym", date(2024, 1, 10), 6),
            _event("Office", date(2024, 1, 10), 9),
        ],
        wardrobe_items=_wardrobe_fixtures(),
        expectations={"min_outfits": 1},
    ),
]
