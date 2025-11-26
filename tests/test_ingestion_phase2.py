"""Phase 2 ingestion flow tests."""

from __future__ import annotations

from pathlib import Path
from typing import Dict

import pytest

from adk_app.config import ADKConfig
from agents.wardrobe_ingestion import WardrobeIngestionAgent
from models.ingestion_mapping import map_raw_metadata_to_wardrobe_item
from tools.product_page_fetcher import (
    InvalidProductURLError,
    ProductPageFetchError,
    fetch_product_page,
)
from tools.product_parser import parse_product_html
from tools.wardrobe_store import SQLiteWardrobeStore
from tools.wardrobe_tools import WardrobeTools


def test_fetch_product_page_success(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: Dict[str, object] = {}

    class FakeResponse:
        status_code = 200
        text = "<html>ok</html>"

    def fake_get(url: str, timeout: float = 10.0):
        calls["url"] = url
        calls["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr("tools.product_page_fetcher.requests.get", fake_get)
    html = fetch_product_page("https://example.com/product/123", timeout=5)
    assert "ok" in html
    assert calls == {"url": "https://example.com/product/123", "timeout": 5}


def test_fetch_product_page_invalid_url() -> None:
    with pytest.raises(InvalidProductURLError):
        fetch_product_page("ftp://example.com/bad")


def test_fetch_product_page_non_200(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeResponse:
        status_code = 404
        text = "not found"

    monkeypatch.setattr(
        "tools.product_page_fetcher.requests.get", lambda *args, **kwargs: FakeResponse()
    )
    with pytest.raises(ProductPageFetchError):
        fetch_product_page("https://example.com/missing")


def test_parse_product_html_with_open_graph() -> None:
    html = """
    <html>
      <head>
        <meta property="og:title" content="Cozy Wool Coat" />
        <meta property="og:image" content="/images/coat.jpg" />
        <meta property="product:brand" content="Zara" />
        <meta property="product:color" content="Navy" />
      </head>
    </html>
    """
    parsed = parse_product_html(html, url="https://shop.test/coat")
    assert parsed["title"] == "Cozy Wool Coat"
    assert parsed["image_url"].endswith("/images/coat.jpg")
    assert parsed["brand"] == "Zara"
    assert parsed["colors"] == ["Navy"]


def test_parse_product_html_with_basic_tags() -> None:
    html = """
    <html>
      <head><title>Bright Tee</title></head>
      <body>
        <h1>Bright Tee - Organic Cotton</h1>
        <img src="/assets/tee.png" />
      </body>
    </html>
    """
    parsed = parse_product_html(html, url="https://shop.test/tee")
    assert parsed["title"] == "Bright Tee"
    assert parsed["image_url"].endswith("/assets/tee.png")
    assert "Bright" in parsed["description"]


def test_map_raw_metadata_to_wardrobe_item_infers_category_and_colors() -> None:
    raw = {
        "title": "Blue Linen Shirt",
        "description": "Lightweight cotton-linen blend shirt",
        "image_url": "https://img.test/shirt.jpg",
        "colors": ["blue"],
    }
    item = map_raw_metadata_to_wardrobe_item(
        user_id="user-1", source_url="https://shop.test/shirt", raw=raw
    )
    assert item.category == "top"
    assert item.sub_category == "shirt"
    assert "blue" in item.colors
    assert "linen" in item.materials or "cotton" in item.materials
    assert item.season_tags


def test_map_raw_metadata_to_wardrobe_item_missing_category() -> None:
    raw = {"title": "Mystery item", "image_url": "https://img.test/unknown.jpg"}
    with pytest.raises(ValueError):
        map_raw_metadata_to_wardrobe_item(user_id="user-1", source_url="url", raw=raw)


def test_ingestion_flow_persists_items(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    sample_html = """
    <html><body><h1>Denim Jeans</h1><img src="/jeans.jpg" /></body></html>
    """

    def fake_fetch(url: str, timeout: float | None = None) -> str:  # noqa: ARG001
        return sample_html

    monkeypatch.setattr("agents.wardrobe_ingestion.fetch_product_page", fake_fetch)

    config = ADKConfig(project_id="test-project", api_key=None)
    store = SQLiteWardrobeStore(database_path=tmp_path / "wardrobe.db")
    wardrobe_tools = WardrobeTools(store)
    agent = WardrobeIngestionAgent(config=config, wardrobe_tools=wardrobe_tools, tools=[])

    result = agent.ingest(user_id="user-1", urls=["https://shop.test/jeans"])
    assert result["failures"] == []
    assert len(result["items"]) == 1

    stored_items = store.list_items_for_user("user-1")
    assert len(stored_items) == 1
    assert stored_items[0].sub_category == "jeans"

