"""Lightweight deterministic embedding helpers for text and wardrobe items."""

from __future__ import annotations

import hashlib
import re
from dataclasses import asdict
from typing import Iterable, List

from models.wardrobe_item import WardrobeItem


class EmbeddingHelper:
    """Creates repeatable embeddings for text and wardrobe items."""

    def __init__(self, dimension: int = 128) -> None:
        if dimension <= 0:
            raise ValueError("Embedding dimension must be positive")
        self.dimension = dimension

    @staticmethod
    def _tokenise(text: str) -> List[str]:
        return [token for token in re.split(r"[^a-zA-Z0-9]+", text.lower()) if token]

    def _hash_to_index(self, token: str) -> int:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        return int.from_bytes(digest[:4], "big") % self.dimension

    def _accumulate_tokens(self, tokens: Iterable[str]) -> List[float]:
        vector = [0.0] * self.dimension
        for token in tokens:
            idx = self._hash_to_index(token)
            vector[idx] += 1.0
        return vector

    def text_embedding(self, text: str) -> List[float]:
        """Embed text using a simple hashed bag-of-words scheme."""

        if not text:
            return [0.0] * self.dimension
        tokens = self._tokenise(text)
        return self._accumulate_tokens(tokens)

    def image_embedding(self, image_url: str) -> List[float]:
        """Embed an image URL to allow mixing into item representations."""

        if not image_url:
            return [0.0] * self.dimension
        return self._accumulate_tokens([image_url])

    def item_embedding(self, item: WardrobeItem) -> List[float]:
        """Create an embedding from the salient wardrobe item metadata."""

        metadata = asdict(item)
        text_bits = [
            metadata.get("category", ""),
            metadata.get("sub_category", ""),
            " ".join(metadata.get("colors", []) or []),
            " ".join(metadata.get("materials", []) or []),
            metadata.get("brand", ""),
            metadata.get("fit", ""),
            " ".join(metadata.get("season_tags", []) or []),
            " ".join(metadata.get("style_tags", []) or []),
            metadata.get("user_notes", ""),
        ]
        combined_text = " ".join(bit for bit in text_bits if bit)
        text_vector = self.text_embedding(combined_text)
        image_vector = self.image_embedding(metadata.get("image_url", ""))
        return [t + i for t, i in zip(text_vector, image_vector)]


__all__ = ["EmbeddingHelper"]
