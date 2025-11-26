import sys
import types
from pathlib import Path
from typing import Any, Dict, Tuple

import pytest


def _install_genai_stubs() -> None:
    """Install lightweight stubs for google generative AI modules if missing."""

    if "google.generativeai.agent" in sys.modules:
        return

    class _DummyTool:
        def __init__(self, *_, **kwargs):
            self.name = kwargs.get("name")
            self.func = kwargs.get("func")

    class _DummyLlmAgent:
        def __init__(self, *_, name: str | None = None, tools=None, **__):
            self.name = name or "agent"
            self.tools = tools or []

    class _DummyApp:
        def __init__(self, *_, **__):
            self.registry: list = []

        def register(self, component: object) -> None:
            self.registry.append(component)

    _google_module = types.ModuleType("google")
    _genai_module = types.ModuleType("google.generativeai")
    _genai_agent_module = types.ModuleType("google.generativeai.agent")

    _genai_agent_module.Tool = _DummyTool
    _genai_agent_module.LlmAgent = _DummyLlmAgent
    _genai_agent_module.App = _DummyApp

    def _noop_configure(**_: Dict) -> None:
        return None

    _genai_module.agent = _genai_agent_module
    _genai_module.configure = _noop_configure
    _google_module.generativeai = _genai_module

    sys.modules.setdefault("google", _google_module)
    sys.modules.setdefault("google.generativeai", _genai_module)
    sys.modules.setdefault("google.generativeai.agent", _genai_agent_module)


_install_genai_stubs()

sys.path.append(str(Path(__file__).resolve().parents[1]))

from adk_app.config import ADKConfig
from agents.wardrobe_query import WardrobeQueryAgent
from tools.wardrobe_tools import WardrobeTools
from tools.wardrobe_store import SQLiteWardrobeStore


class DummyTool:
    def __init__(self, name: str, func) -> None:
        self.name = name
        self.func = func


@pytest.fixture()
def agent_fixture(tmp_path: Path) -> Tuple[WardrobeQueryAgent, WardrobeTools, Dict[str, int]]:
    store = SQLiteWardrobeStore(tmp_path / "wardrobe.db")
    wardrobe_tools = WardrobeTools(store)
    call_counts: Dict[str, int] = {"search": 0, "list": 0}

    def _wrap(method_name: str, counter_key: str):
        method = getattr(wardrobe_tools, method_name)

        def _inner(*args: Any, **kwargs: Any):
            call_counts[counter_key] += 1
            return method(*args, **kwargs)

        return _inner

    tools = [
        DummyTool("search_wardrobe_items", _wrap("search_wardrobe_items", "search")),
        DummyTool("list_wardrobe_items", _wrap("list_wardrobe_items", "list")),
    ]

    agent = WardrobeQueryAgent(config=ADKConfig(project_id="test"), tools=tools)
    return agent, wardrobe_tools, call_counts


def _add_item(
    tools: WardrobeTools,
    user_id: str,
    item_id: str,
    category: str,
    sub_category: str,
    style_tags: list[str],
    season_tags: list[str],
    colors: list[str],
) -> None:
    tools.add_wardrobe_item(
        user_id,
        {
            "item_id": item_id,
            "image_url": f"https://example.com/{item_id}.jpg",
            "source_url": "https://example.com/product",
            "category": category,
            "sub_category": sub_category,
            "style_tags": style_tags,
            "season_tags": season_tags,
            "materials": ["cotton"],
            "colors": colors,
        },
    )


def test_query_filters_formality_season_and_exclusions(agent_fixture: Tuple[WardrobeQueryAgent, WardrobeTools, Dict[str, int]]):
    agent, tools, call_counts = agent_fixture
    user_id = "user-1"

    _add_item(tools, user_id, "biz-top", "top", "shirt", ["business"], ["cold_weather"], ["navy"])
    _add_item(tools, user_id, "casual-hoodie", "top", "hoodie", ["casual"], ["cold_weather"], ["gray"])
    _add_item(tools, user_id, "summer-dress", "dress", "day_dress", ["party"], ["warm_weather"], ["red"])
    _add_item(tools, user_id, "business-boots", "shoes", "boots", ["business"], ["cold_weather"], ["black"])

    event_profile = {
        "formality": "business",
        "activity_type": "office",
        "season": "cold_weather",
        "exclusions": ["casual-hoodie"],
    }

    results = agent.query(
        event_profile=event_profile,
        user_id=user_id,
        mood="neutral",
        weather_profile={"season": "cold_weather"},
        user_preferences={"disliked_colors": ["red"]},
    )

    assert set(results) == {"biz-top", "business-boots"}
    assert call_counts["search"] >= 1


def test_activity_filter_prioritises_sporty(agent_fixture: Tuple[WardrobeQueryAgent, WardrobeTools, Dict[str, int]]):
    agent, tools, call_counts = agent_fixture
    user_id = "user-2"

    _add_item(tools, user_id, "sport-shorts", "bottom", "shorts", ["sporty", "casual"], ["warm_weather"], ["blue"])
    _add_item(tools, user_id, "formal-heels", "shoes", "heels", ["formal"], ["all_year"], ["black"])
    _add_item(tools, user_id, "sport-sneakers", "shoes", "sneakers", ["sporty", "casual"], ["all_year"], ["white"])

    event_profile = {"activity_type": "fitness", "formality": "informal", "season": "warm_weather"}
    results = agent.query(event_profile=event_profile, user_id=user_id, mood="happy")

    assert set(results) == {"sport-shorts", "sport-sneakers"}
    assert call_counts["search"] >= 1
