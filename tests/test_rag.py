"""Unit tests for the wardrobe RAG index."""

from __future__ import annotations

from pathlib import Path

import pytest

from models.wardrobe_item import WardrobeItem
from tools.embeddings import EmbeddingHelper
from tools.rag import WardrobeRAG


def _make_item(item_id: str, user_id: str, **overrides):
    base = dict(
        item_id=item_id,
        user_id=user_id,
        image_url=f"https://example.com/{item_id}.jpg",
        source_url=f"https://store/{item_id}",
        category="top",
        sub_category="shirt",
        colors=["blue"],
        materials=["cotton"],
        brand="Example",
        fit="relaxed",
        season_tags=["warm_weather"],
        style_tags=["casual"],
    )
    base.update(overrides)
    return WardrobeItem(**base)


def test_index_and_search_returns_ranked_items(tmp_path: Path):
    rag = WardrobeRAG(database_path=tmp_path / "rag.db", embedding_helper=EmbeddingHelper(32))
    denim = _make_item(
        "denim_jacket",
        "user-1",
        category="outerwear",
        sub_category="jacket",
        colors=["blue"],
        user_notes="Denim jacket with soft lining",
    )
    sneakers = _make_item(
        "running_sneaker",
        "user-1",
        category="shoes",
        sub_category="sneakers",
        colors=["white"],
        user_notes="Lightweight running sneakers",
    )

    rag.index_items([denim, sneakers])

    results = rag.search("denim jacket", user_id="user-1")
    assert results
    assert results[0].item_id == "denim_jacket"
    assert {item.item_id for item in results} == {"denim_jacket", "running_sneaker"}


def test_search_filters_by_user(tmp_path: Path):
    rag = WardrobeRAG(database_path=tmp_path / "rag.db", embedding_helper=EmbeddingHelper(16))
    rag.index_items([
        _make_item("user1_item", "user-a", user_notes="formal blazer"),
        _make_item("user2_item", "user-b", user_notes="sport shorts"),
    ])

    results = rag.search("blazer", user_id="user-a")
    assert results
    assert all(item.user_id == "user-a" for item in results)
    assert {item.item_id for item in results} == {"user1_item"}


def test_search_empty_index_returns_empty(tmp_path: Path):
    rag = WardrobeRAG(database_path=tmp_path / "rag.db", embedding_helper=EmbeddingHelper(8))
    assert rag.search("anything", user_id="nobody") == []


def test_indexing_stores_embeddings(tmp_path: Path):
    helper = EmbeddingHelper(8)
    rag = WardrobeRAG(database_path=tmp_path / "rag.db", embedding_helper=helper)
    explicit_vector = [1.0] * 8
    item = _make_item("with_vector", "user-c", embedding=explicit_vector, user_notes="vector set")

    rag.index_items([item])

    # Fetch raw row to verify persistence
    rows = rag._load_items_for_user("user-c")
    assert len(rows) == 1
    stored = rag._deserialise_vector(rows[0]["embedding"])
    assert stored == explicit_vector

