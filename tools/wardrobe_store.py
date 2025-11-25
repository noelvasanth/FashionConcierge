"""Wardrobe storage abstractions."""

from abc import ABC, abstractmethod
from typing import Iterable, List

from models.wardrobe import WardrobeItem


class WardrobeStore(ABC):
    """Abstract interface for wardrobe persistence and retrieval."""

    @abstractmethod
    def save_items(self, items: Iterable[WardrobeItem]) -> None:
        """Persist wardrobe items."""

    @abstractmethod
    def list_items(self, user_id: str) -> List[WardrobeItem]:
        """Return stored wardrobe items for the user."""

    @abstractmethod
    def search(self, query: str, user_id: str) -> List[WardrobeItem]:
        """Run a simple search over wardrobe items."""


class SQLiteWardrobeStore(WardrobeStore):
    """Local SQLite-backed store placeholder."""

    def __init__(self, database_path: str = "wardrobe.db") -> None:
        self.database_path = database_path

    def save_items(self, items: Iterable[WardrobeItem]) -> None:  # pragma: no cover - stub
        for _ in items:
            pass

    def list_items(self, user_id: str) -> List[WardrobeItem]:  # pragma: no cover - stub
        return []

    def search(self, query: str, user_id: str) -> List[WardrobeItem]:  # pragma: no cover - stub
        return []
