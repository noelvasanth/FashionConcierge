"""Minimal local stand-in for BeautifulSoup for offline parsing.

This lightweight implementation supports the subset of the BeautifulSoup API
used in this project: ``find`` lookups by tag name and attributes, attribute
access via ``get`` and ``__getitem__``, and ``text`` aggregation. It is **not**
a drop-in replacement for full BeautifulSoup but keeps parsing deterministic for
tests in offline environments.
"""

from __future__ import annotations

from html.parser import HTMLParser
from typing import Dict, List, Optional


class _Node:
    def __init__(self, name: str, attrs: Optional[Dict[str, str]] = None, parent: Optional["_Node"] = None) -> None:
        self.name = name
        self.attrs = attrs or {}
        self.parent = parent
        self.children: List[_Node] = []
        self.text_parts: List[str] = []

    @property
    def text(self) -> str:
        parts = list(self.text_parts)
        for child in self.children:
            parts.append(child.text)
        return "".join(parts)

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        return self.attrs.get(key, default)

    def __getitem__(self, key: str) -> str:
        return self.attrs[key]


class _SoupParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.root = _Node("document", {})
        self._stack: List[_Node] = [self.root]

    def handle_starttag(self, tag: str, attrs: List[tuple[str, Optional[str]]]) -> None:  # type: ignore[override]
        attr_dict = {k: v for k, v in attrs if v is not None}
        node = _Node(tag, attr_dict, parent=self._stack[-1])
        self._stack[-1].children.append(node)
        self._stack.append(node)

    def handle_endtag(self, tag: str) -> None:  # type: ignore[override]
        if len(self._stack) > 1:
            self._stack.pop()

    def handle_data(self, data: str) -> None:  # type: ignore[override]
        if data.strip():
            self._stack[-1].text_parts.append(data)


class BeautifulSoup:
    def __init__(self, html: str, parser: str = "html.parser") -> None:  # noqa: ARG002
        soup_parser = _SoupParser()
        soup_parser.feed(html)
        self._root = soup_parser.root

    def find(self, name: str, attrs: Optional[Dict[str, object]] = None, **kwargs: object) -> Optional[_Node]:
        merged_attrs: Dict[str, object] = {}
        if attrs:
            merged_attrs.update(attrs)
        merged_attrs.update({k: v for k, v in kwargs.items()})
        return self._find_recursive(self._root, name, merged_attrs)

    def _find_recursive(self, node: _Node, name: str, attrs: Dict[str, object]) -> Optional[_Node]:
        if node.name == name and self._matches(node, attrs):
            return node
        for child in node.children:
            found = self._find_recursive(child, name, attrs)
            if found:
                return found
        return None

    def _matches(self, node: _Node, attrs: Dict[str, object]) -> bool:
        for key, value in attrs.items():
            attr_val = node.attrs.get(key)
            if value is True and attr_val is None:
                return False
            if value is not True and attr_val != value:
                return False
        return True


__all__ = ["BeautifulSoup"]
