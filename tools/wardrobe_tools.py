"""ADK tool wrappers for wardrobe storage."""

from __future__ import annotations

from dataclasses import asdict
from functools import partial
from typing import Any, Dict, List, Optional

from adk_app.genai_fallback import ensure_genai_imports
ensure_genai_imports()

from google.generativeai import agent as genai_agent

from models.wardrobe_item import WardrobeItem, from_raw_metadata
from tools.wardrobe_store import SQLiteWardrobeStore, WardrobeStore
from tools.observability import instrument_tool


def _default_store() -> SQLiteWardrobeStore:
    return SQLiteWardrobeStore()


class WardrobeTools:
    """Thin wrapper to expose WardrobeStore operations as ADK tools."""

    def __init__(self, store: Optional[WardrobeStore] = None) -> None:
        self.store = store or _default_store()

    @instrument_tool("add_wardrobe_item")
    def add_wardrobe_item(self, user_id: str, item_data: Dict[str, Any]) -> Dict[str, Any]:
        item = from_raw_metadata({**item_data, "user_id": user_id})
        stored = self.store.create_item(item)
        return asdict(stored)

    @instrument_tool("get_wardrobe_item")
    def get_wardrobe_item(self, user_id: str, item_id: str) -> Optional[Dict[str, Any]]:
        item = self.store.get_item(user_id, item_id)
        return asdict(item) if item else None

    @instrument_tool("list_wardrobe_items")
    def list_wardrobe_items(self, user_id: str) -> List[Dict[str, Any]]:
        return [asdict(item) for item in self.store.list_items_for_user(user_id)]

    @instrument_tool("search_wardrobe_items")
    def search_wardrobe_items(self, user_id: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [asdict(item) for item in self.store.search_items(user_id, filters or {})]

    def tool_defs(self) -> List[genai_agent.Tool]:
        """Return ADK Tool definitions for registration."""

        return [
            genai_agent.Tool(
                name="add_wardrobe_item",
                description="Add a wardrobe item for the user.",
                func=partial(self.add_wardrobe_item),
            ),
            genai_agent.Tool(
                name="get_wardrobe_item",
                description="Fetch a wardrobe item by id for the user.",
                func=partial(self.get_wardrobe_item),
            ),
            genai_agent.Tool(
                name="list_wardrobe_items",
                description="List all wardrobe items for the user.",
                func=partial(self.list_wardrobe_items),
            ),
            genai_agent.Tool(
                name="search_wardrobe_items",
                description="Search wardrobe items by category, style, season or color.",
                func=partial(self.search_wardrobe_items),
            ),
        ]


__all__ = ["WardrobeTools"]
