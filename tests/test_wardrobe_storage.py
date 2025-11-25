"""Phase one wardrobe storage, taxonomy and tool tests."""

from __future__ import annotations

import sys
import types
from pathlib import Path
from typing import Dict

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

from models import taxonomy
from models.wardrobe_item import WardrobeItem, from_raw_metadata
from tools.wardrobe_store import SQLiteWardrobeStore
from tools.wardrobe_tools import WardrobeTools


@pytest.fixture()
def sample_metadata() -> Dict[str, object]:
    return {
        "item_id": "item-1",
        "user_id": "user-123",
        "image_url": "https://example.com/image.jpg",
        "source_url": "https://example.com/product",
        "category": "Top",
        "sub_category": "Blazer",
        "colors": ["navy blue", "white"],
        "materials": ["cotton"],
        "brand": "Example",
        "fit": "relaxed",
        "season_tags": ["Cold_Weather"],
        "style_tags": ["Business"],
        "user_notes": "A smart navy blazer.",
    }


def test_taxonomy_contains_expected_categories() -> None:
    """Ensure canonical categories and subcategories are present."""

    expected_categories = {"top", "bottom", "dress", "shoes", "outerwear", "accessory"}
    assert expected_categories.issubset(taxonomy.CATEGORIES.keys())
    assert "blazer" in taxonomy.CATEGORIES["top"]
    assert "jeans" in taxonomy.CATEGORIES["bottom"]


def test_validate_category_and_subcategory() -> None:
    """Validation helpers accept valid inputs and reject invalid ones."""

    assert taxonomy.validate_category("Top") == "top"
    assert taxonomy.validate_subcategory("top", "blazer") == "blazer"

    with pytest.raises(ValueError):
        taxonomy.validate_category("unknown")
    with pytest.raises(ValueError):
        taxonomy.validate_subcategory("top", "boots")


def test_normalize_color_name_handles_variants() -> None:
    """Color normalisation maps variants to canonical names."""

    assert taxonomy.normalize_color_name("navy blue") == "navy"
    assert taxonomy.normalize_color_name("Light Blue") == "blue"
    assert taxonomy.normalize_color_name("off white") == "white"


def test_wardrobe_item_construction(sample_metadata: Dict[str, object]) -> None:
    """WardrobeItem enforces taxonomy constraints and normalisation."""

    item = WardrobeItem(**sample_metadata)
    assert item.category == "top"
    assert item.sub_category == "blazer"
    assert item.colors == ["navy", "white"]
    assert item.season_tags == ["cold_weather"]
    assert item.style_tags == ["business"]


def test_from_raw_metadata_sets_defaults(sample_metadata: Dict[str, object]) -> None:
    """Factory handles loose metadata and fills defaults."""

    raw = sample_metadata.copy()
    raw.pop("colors")
    raw.pop("materials")
    item = from_raw_metadata(raw)
    assert item.colors == []
    assert item.materials == []


def test_invalid_subcategory_raises() -> None:
    """Invalid category/subcategory combinations raise errors."""

    with pytest.raises(ValueError):
        from_raw_metadata(
            {
                "item_id": "bad",
                "user_id": "user",
                "image_url": "img",
                "source_url": "src",
                "category": "top",
                "sub_category": "boots",
            }
        )


@pytest.fixture()
def store(tmp_path: Path) -> SQLiteWardrobeStore:
    return SQLiteWardrobeStore(tmp_path / "wardrobe.db")


def test_store_creates_table_and_round_trip(store: SQLiteWardrobeStore, sample_metadata: Dict[str, object]) -> None:
    """Creating and retrieving an item round-trips through SQLite."""

    item = from_raw_metadata(sample_metadata)
    store.create_item(item)

    fetched = store.get_item(item.user_id, item.item_id)
    assert fetched == item
    assert store.list_items_for_user(item.user_id) == [item]


def test_store_scopes_items_by_user(store: SQLiteWardrobeStore, sample_metadata: Dict[str, object]) -> None:
    """Listing respects user_id isolation."""

    item_user1 = from_raw_metadata(sample_metadata)
    item_user2 = from_raw_metadata({**sample_metadata, "user_id": "other", "item_id": "item-2"})

    store.create_item(item_user1)
    store.create_item(item_user2)

    assert store.list_items_for_user("user-123") == [item_user1]
    assert store.list_items_for_user("other") == [item_user2]


def test_update_and_delete_item(store: SQLiteWardrobeStore, sample_metadata: Dict[str, object]) -> None:
    """Updates persist and deletions remove the record."""

    item = from_raw_metadata(sample_metadata)
    store.create_item(item)

    updated = store.update_item(item.user_id, item.item_id, {"brand": "Updated", "colors": ["blue"]})
    assert updated is not None
    assert updated.brand == "Updated"
    assert updated.colors == ["blue"]

    assert store.delete_item(item.user_id, item.item_id) is True
    assert store.get_item(item.user_id, item.item_id) is None


def test_search_items_filters_by_category_and_tags(store: SQLiteWardrobeStore, sample_metadata: Dict[str, object]) -> None:
    """Search helper filters by category, colors, season and style tags."""

    warm_business = from_raw_metadata(sample_metadata)
    casual_bottom = from_raw_metadata(
        {
            **sample_metadata,
            "item_id": "item-2",
            "category": "bottom",
            "sub_category": "jeans",
            "style_tags": ["casual"],
            "season_tags": ["all_year"],
            "colors": ["blue"],
        }
    )
    cold_shoes = from_raw_metadata(
        {
            **sample_metadata,
            "item_id": "item-3",
            "category": "shoes",
            "sub_category": "boots",
            "style_tags": ["street"],
            "season_tags": ["cold_weather"],
            "colors": ["black"],
        }
    )

    store.create_item(warm_business)
    store.create_item(casual_bottom)
    store.create_item(cold_shoes)

    assert store.search_items("user-123", {"category": "top"}) == [warm_business]
    assert store.search_items("user-123", {"style_tags": ["street"]}) == [cold_shoes]
    assert store.search_items("user-123", {"season_tags": ["cold_weather"]}) == [warm_business, cold_shoes]
    assert store.search_items("user-123", {"colors": ["blue"], "category": "bottom"}) == [casual_bottom]


def test_wardrobe_tools_round_trip(tmp_path: Path, sample_metadata: Dict[str, object]) -> None:
    """Wardrobe tools wrap store operations for agent access."""

    store = SQLiteWardrobeStore(tmp_path / "tools.db")
    tools = WardrobeTools(store)

    payload = {**sample_metadata, "item_id": "tool-item"}
    added = tools.add_wardrobe_item(sample_metadata["user_id"], payload)

    fetched = tools.get_wardrobe_item(sample_metadata["user_id"], "tool-item")
    assert fetched is not None
    assert fetched["category"] == "top"

    all_items = tools.list_wardrobe_items(sample_metadata["user_id"])
    assert len(all_items) == 1
    search_result = tools.search_wardrobe_items(sample_metadata["user_id"], {"category": "top"})
    assert len(search_result) == 1

    tool_defs = tools.tool_defs()
    assert len(tool_defs) == 4
