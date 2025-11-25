"""RAG utilities for wardrobe similarity search."""

from typing import List

from models.wardrobe import WardrobeItem


class WardrobeRAG:
    """Placeholder RAG interface."""

    def __init__(self) -> None:
        self.index_ready = False

    def index_items(self, items: List[WardrobeItem]) -> None:  # pragma: no cover - stub
        self.index_ready = True

    def search(self, query: str, user_id: str) -> List[WardrobeItem]:  # pragma: no cover - stub
        return []
