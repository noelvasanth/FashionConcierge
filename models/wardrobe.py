"""Compatibility wrapper for wardrobe models.

The canonical :class:`WardrobeItem` lives in ``models.wardrobe_item``. This
module re-exports it to preserve imports from the Phase 0 skeleton.
"""

from models.wardrobe_item import WardrobeItem, from_raw_metadata

__all__ = ["WardrobeItem", "from_raw_metadata"]
