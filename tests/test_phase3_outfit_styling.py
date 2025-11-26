"""Phase 3 tests for outfit styling logic and agent integration."""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import List

sys.path.append(str(Path(__file__).resolve().parents[1]))

from adk_app.config import ADKConfig
from agents.outfit_stylist_agent import OutfitStylistAgent
from logic.outfit_builder import (
    apply_color_harmony,
    build_outfit,
    generate_collage_spec,
    select_candidates_for_mood,
    CandidateSelectionResult,
    OutfitBuildResult,
    HarmonyApplicationResult,
    CollageSpecResult,
)
from models.color_theory import analogous_triplet, choose_harmonious_colors, complementary, monochrome
from models.mood_styles import get_mood_style
from models.wardrobe_item import WardrobeItem
from tools.wardrobe_store import SQLiteWardrobeStore
from tools.wardrobe_tools import WardrobeTools


def _seed_items(store: SQLiteWardrobeStore, user_id: str = "demo") -> List[WardrobeItem]:
    items = [
        WardrobeItem(
            item_id="top1",
            user_id=user_id,
            image_url="http://example.com/top1.jpg",
            source_url="http://example.com/top1",
            category="top",
            sub_category="shirt",
            colors=["red"],
            style_tags=["party"],
            season_tags=["all_year"],
        ),
        WardrobeItem(
            item_id="bottom1",
            user_id=user_id,
            image_url="http://example.com/bottom1.jpg",
            source_url="http://example.com/bottom1",
            category="bottom",
            sub_category="jeans",
            colors=["black"],
            style_tags=["party"],
            season_tags=["all_year"],
        ),
        WardrobeItem(
            item_id="shoes1",
            user_id=user_id,
            image_url="http://example.com/shoes1.jpg",
            source_url="http://example.com/shoes1",
            category="shoes",
            sub_category="sneakers",
            colors=["white"],
            style_tags=["party"],
            season_tags=["all_year"],
        ),
        WardrobeItem(
            item_id="outer1",
            user_id=user_id,
            image_url="http://example.com/outer1.jpg",
            source_url="http://example.com/outer1",
            category="outerwear",
            sub_category="jacket",
            colors=["blue"],
            style_tags=["street"],
            season_tags=["all_year"],
        ),
        WardrobeItem(
            item_id="accessory1",
            user_id=user_id,
            image_url="http://example.com/acc1.jpg",
            source_url="http://example.com/acc1",
            category="accessory",
            sub_category="hat",
            colors=["green"],
            style_tags=["street"],
            season_tags=["all_year"],
        ),
    ]
    for item in items:
        store.create_item(item)
    return items


def test_mood_styles_profile_structure():
    profile = get_mood_style("festive")
    assert profile.name == "festive"
    assert profile.style_tags
    assert profile.palette
    assert re.match(r"^#[0-9A-Fa-f]{6}$", profile.background_color)


def test_color_theory_rules():
    assert monochrome(["red", "Red"]) is True
    assert complementary("blue", "orange") is True
    assert analogous_triplet(["red", "orange", "yellow"]) is True
    harmony = choose_harmonious_colors(["red", "green", "blue"], ["red", "gold"])
    assert harmony.chosen_colors[0] == "red"
    assert harmony.rule_used in {"monochrome", "complementary", "analogous", "complementary-to-palette", "none"}


def test_outfit_builder_flow(tmp_path):
    db_path = tmp_path / "wardrobe.db"
    store = SQLiteWardrobeStore(db_path)
    tools = WardrobeTools(store)
    _seed_items(store)

    candidates: CandidateSelectionResult = select_candidates_for_mood("demo", "festive", tools)
    assert {item.category for item in candidates.items}.issuperset({"top", "bottom", "shoes"})
    assert candidates.diagnostics["initial_count"] == 5

    mood_profile = get_mood_style("festive")
    outfit: OutfitBuildResult = build_outfit(candidates.items, mood_profile)
    categories = [item.category for item in outfit.items]
    assert ["top", "bottom", "shoes"] == categories[:3]
    assert outfit.diagnostics["combinations_scored"] >= 1

    harmonised: HarmonyApplicationResult = apply_color_harmony(outfit.items, mood_profile)
    assert all(item.category in categories for item in harmonised.items)
    assert harmonised.diagnostics["chosen_colors"]

    collage: CollageSpecResult = generate_collage_spec(harmonised.items, mood_profile)
    assert "background_color" in collage.collage and collage.collage["stickers"]
    assert 0 <= collage.collage["stickers"][0]["x"] <= 1
    assert collage.diagnostics["layout"][0]["item_id"] == harmonised.items[0].item_id


def test_outfit_stylist_agent_integration(tmp_path):
    db_path = tmp_path / "wardrobe.db"
    store = SQLiteWardrobeStore(db_path)
    tools = WardrobeTools(store)
    _seed_items(store, user_id="agent_user")

    config = ADKConfig.from_env()
    agent = OutfitStylistAgent(config=config, wardrobe_tools=tools)

    response = agent.recommend_outfit(user_id="agent_user", mood="festive", top_n=1)
    assert response["ranked_outfits"]
    first = response["ranked_outfits"][0]
    categories = {item["category"] for item in first["items"]}
    assert {"top", "bottom", "shoes"}.issubset(categories)
    collage = first["collage"]
    assert collage["background_color"] == get_mood_style("festive").background_color
    assert response["user_facing_rationale"]
    debug_summary = response.get("debug_summary", {})
    assert debug_summary.get("candidate_outfits") >= 1
