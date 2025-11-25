"""Canonical taxonomy definitions."""

from typing import Dict, List

CATEGORIES: Dict[str, List[str]] = {
    "top": ["t-shirt", "shirt", "blouse", "sweater", "blazer"],
    "bottom": ["jeans", "trousers", "skirt", "shorts"],
    "dress": ["day-dress", "evening-dress"],
    "shoes": ["sneakers", "boots", "heels", "loafers"],
    "outerwear": ["coat", "jacket", "cardigan"],
    "accessory": ["belt", "bag", "hat", "scarf"],
}

STYLE_TAGS = ["casual", "business", "formal", "party", "street", "sporty"]
SEASON_TAGS = ["warm_weather", "cold_weather", "all_year"]
MOODS = ["happy", "neutral", "trendy", "casual", "festive", "urban"]

MOOD_PALETTES: Dict[str, List[str]] = {
    "happy": ["#fbe7c6", "#ffd972", "#ff9b71"],
    "neutral": ["#f5f5f5", "#d0d4d8", "#9ea3a8"],
    "trendy": ["#a1c4fd", "#c2e9fb", "#d4a5a5"],
    "casual": ["#c8d5b9", "#8fc0a9", "#68b0ab"],
    "festive": ["#f4b942", "#e77f67", "#c44536"],
    "urban": ["#1f1f1f", "#3d3d3d", "#7f8487"],
}
