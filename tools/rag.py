"""RAG utilities for wardrobe similarity search using local embeddings."""

from __future__ import annotations

import json
import math
import sqlite3
from dataclasses import asdict
from pathlib import Path
from typing import Iterable, List

from models.wardrobe import WardrobeItem
from tools.embeddings import EmbeddingHelper


class WardrobeRAG:
    """SQLite-backed similarity index for wardrobe items."""

    def __init__(
        self,
        database_path: str | Path = "data/rag_index.db",
        embedding_helper: EmbeddingHelper | None = None,
    ) -> None:
        self.database_path = Path(database_path)
        if self.database_path.parent and not self.database_path.parent.exists():
            self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.embedding_helper = embedding_helper or EmbeddingHelper()
        self._ensure_tables()
        self.index_ready = False

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.database_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_tables(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS rag_index (
                    user_id TEXT NOT NULL,
                    item_id TEXT NOT NULL,
                    embedding TEXT NOT NULL,
                    metadata TEXT NOT NULL,
                    PRIMARY KEY (user_id, item_id)
                );
                """
            )

    @staticmethod
    def _serialise_vector(values: Iterable[float]) -> str:
        return json.dumps(list(values))

    @staticmethod
    def _deserialise_vector(raw: str) -> List[float]:
        return [float(value) for value in json.loads(raw)] if raw else []

    @staticmethod
    def _cosine_similarity(a: List[float], b: List[float]) -> float:
        if not a or not b or len(a) != len(b):
            return 0.0
        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))
        if not norm_a or not norm_b:
            return 0.0
        return dot_product / (norm_a * norm_b)

    def index_items(self, items: List[WardrobeItem]) -> None:
        """Upsert wardrobe items into the local embedding index."""

        if not items:
            return

        with self._connect() as conn:
            for item in items:
                embedding = item.embedding or self.embedding_helper.item_embedding(item)
                metadata = asdict(item)
                metadata["embedding"] = embedding
                conn.execute(
                    """
                    INSERT OR REPLACE INTO rag_index (user_id, item_id, embedding, metadata)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        item.user_id,
                        item.item_id,
                        self._serialise_vector(embedding),
                        json.dumps(metadata),
                    ),
                )
        self.index_ready = True

    def _load_items_for_user(self, user_id: str) -> List[sqlite3.Row]:
        with self._connect() as conn:
            cursor = conn.execute(
                "SELECT * FROM rag_index WHERE user_id = ?",
                (user_id,),
            )
            return cursor.fetchall()

    def search(self, query: str, user_id: str, top_k: int = 5) -> List[WardrobeItem]:
        """Run a similarity query against indexed wardrobe items for a user."""

        if not query:
            return []

        query_vector = self.embedding_helper.text_embedding(query)
        rows = self._load_items_for_user(user_id)
        if not rows:
            return []

        scored_items: list[tuple[float, WardrobeItem]] = []
        for row in rows:
            embedding = self._deserialise_vector(row["embedding"])
            metadata = json.loads(row["metadata"]) if row["metadata"] else {}
            item = WardrobeItem(**metadata)
            similarity = self._cosine_similarity(query_vector, embedding)
            scored_items.append((similarity, item))

        scored_items.sort(key=lambda pair: pair[0], reverse=True)
        ranked = [item for score, item in scored_items if score > 0][:top_k]
        return ranked


__all__ = ["WardrobeRAG"]
