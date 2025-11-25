"""Wardrobe storage abstractions and SQLite implementation."""
from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from pathlib import Path
from typing import Dict, List, Optional

from models.taxonomy import normalize_color_name, validate_category
from models.wardrobe_item import WardrobeItem


class WardrobeStore:
    """Persistence interface for wardrobe items."""

    def create_item(self, item: WardrobeItem) -> WardrobeItem:
        raise NotImplementedError

    def get_item(self, user_id: str, item_id: str) -> Optional[WardrobeItem]:
        raise NotImplementedError

    def list_items_for_user(self, user_id: str) -> List[WardrobeItem]:
        raise NotImplementedError

    def update_item(self, user_id: str, item_id: str, updated_fields: Dict[str, object]) -> Optional[WardrobeItem]:
        raise NotImplementedError

    def delete_item(self, user_id: str, item_id: str) -> bool:
        raise NotImplementedError

    def search_items(self, user_id: str, filters: Dict[str, object]) -> List[WardrobeItem]:
        raise NotImplementedError


class SQLiteWardrobeStore(WardrobeStore):
    """Local SQLite-backed store for wardrobe items."""

    def __init__(self, database_path: str | Path = "data/wardrobe.db") -> None:
        self.database_path = Path(database_path)
        if self.database_path.parent and not self.database_path.parent.exists():
            self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_tables()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.database_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_tables(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS wardrobe_items (
                    user_id TEXT NOT NULL,
                    item_id TEXT NOT NULL,
                    image_url TEXT,
                    source_url TEXT,
                    category TEXT,
                    sub_category TEXT,
                    colors TEXT,
                    materials TEXT,
                    brand TEXT,
                    fit TEXT,
                    season_tags TEXT,
                    style_tags TEXT,
                    user_notes TEXT,
                    embedding TEXT,
                    PRIMARY KEY (user_id, item_id)
                );
                """
            )

    @staticmethod
    def _serialise_list(values: Optional[List[object]]) -> str:
        return json.dumps(values or [])

    @staticmethod
    def _deserialise_list(raw: str) -> List[object]:
        return json.loads(raw) if raw else []

    def create_item(self, item: WardrobeItem) -> WardrobeItem:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO wardrobe_items (
                    user_id, item_id, image_url, source_url, category, sub_category,
                    colors, materials, brand, fit, season_tags, style_tags, user_notes, embedding
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.user_id,
                    item.item_id,
                    item.image_url,
                    item.source_url,
                    item.category,
                    item.sub_category,
                    self._serialise_list(item.colors),
                    self._serialise_list(item.materials),
                    item.brand,
                    item.fit,
                    self._serialise_list(item.season_tags),
                    self._serialise_list(item.style_tags),
                    item.user_notes,
                    self._serialise_list(item.embedding),
                ),
            )
        return item

    def _row_to_item(self, row: sqlite3.Row) -> WardrobeItem:
        return WardrobeItem(
            item_id=row["item_id"],
            user_id=row["user_id"],
            image_url=row["image_url"],
            source_url=row["source_url"],
            category=row["category"],
            sub_category=row["sub_category"],
            colors=self._deserialise_list(row["colors"]),
            materials=self._deserialise_list(row["materials"]),
            brand=row["brand"],
            fit=row["fit"],
            season_tags=self._deserialise_list(row["season_tags"]),
            style_tags=self._deserialise_list(row["style_tags"]),
            user_notes=row["user_notes"],
            embedding=[float(x) for x in self._deserialise_list(row["embedding"])] or None,
        )

    def get_item(self, user_id: str, item_id: str) -> Optional[WardrobeItem]:
        with self._connect() as conn:
            cursor = conn.execute(
                "SELECT * FROM wardrobe_items WHERE user_id = ? AND item_id = ?",
                (user_id, item_id),
            )
            row = cursor.fetchone()
            return self._row_to_item(row) if row else None

    def list_items_for_user(self, user_id: str) -> List[WardrobeItem]:
        with self._connect() as conn:
            cursor = conn.execute(
                "SELECT * FROM wardrobe_items WHERE user_id = ? ORDER BY item_id",
                (user_id,),
            )
            return [self._row_to_item(row) for row in cursor.fetchall()]

    def update_item(self, user_id: str, item_id: str, updated_fields: Dict[str, object]) -> Optional[WardrobeItem]:
        current = self.get_item(user_id, item_id)
        if not current:
            return None

        for key, value in updated_fields.items():
            if key in {"user_id", "item_id"}:
                continue
            if hasattr(current, key):
                setattr(current, key, value)

        validated = WardrobeItem(**asdict(current))
        return self.create_item(validated)

    def delete_item(self, user_id: str, item_id: str) -> bool:
        with self._connect() as conn:
            cursor = conn.execute(
                "DELETE FROM wardrobe_items WHERE user_id = ? AND item_id = ?",
                (user_id, item_id),
            )
            return cursor.rowcount > 0

    def search_items(self, user_id: str, filters: Dict[str, object]) -> List[WardrobeItem]:
        items = self.list_items_for_user(user_id)
        category_key = None
        if filters and filters.get("category"):
            try:
                category_key = validate_category(str(filters["category"]))
            except ValueError:
                return []

        colors = {normalize_color_name(str(c)) for c in (filters.get("colors", []) or [])} if filters else set()
        style_tags = {str(tag).strip().lower().replace(" ", "_") for tag in (filters.get("style_tags", []) or [])} if filters else set()
        season_tags = {str(tag).strip().lower().replace(" ", "_") for tag in (filters.get("season_tags", []) or [])} if filters else set()

        def matches(item: WardrobeItem) -> bool:
            if category_key and item.category != category_key:
                return False
            if colors and not colors.intersection(set(item.colors)):
                return False
            if style_tags and not style_tags.intersection(set(item.style_tags)):
                return False
            if season_tags and not season_tags.intersection(set(item.season_tags)):
                return False
            return True

        return [item for item in items if matches(item)]


__all__ = ["WardrobeStore", "SQLiteWardrobeStore"]
