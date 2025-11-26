"""Tests for the quality critic rule-based checks."""

from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from agents.quality_critic import QualityCriticAgent
from adk_app.config import ADKConfig


def _build_agent() -> QualityCriticAgent:
    return QualityCriticAgent(config=ADKConfig(project_id="test"))


def test_quality_critic_flags_conflicts_and_repetition() -> None:
    """High-risk context should surface weather and reuse issues."""

    outfits = [
        {
            "items": [
                {"item_id": "top-1", "category": "top", "sub_category": "tee", "style_tags": ["casual"]},
                {
                    "item_id": "bottom-1",
                    "category": "bottom",
                    "sub_category": "jeans",
                    "style_tags": ["casual"],
                },
                {
                    "item_id": "shoes-1",
                    "category": "shoes",
                    "sub_category": "sandals",
                    "style_tags": ["casual"],
                },
            ]
        },
        {
            "items": [
                {"item_id": "top-1", "category": "top", "sub_category": "tee", "style_tags": ["casual"]},
                {
                    "item_id": "bottom-2",
                    "category": "bottom",
                    "sub_category": "chinos",
                    "style_tags": ["business"],
                },
                {
                    "item_id": "shoes-2",
                    "category": "shoes",
                    "sub_category": "derby",
                    "style_tags": ["business"],
                },
            ]
        },
    ]

    context = {
        "warmth_requirement": "high",
        "weather_risk_level": "high",
        "formality_requirement": "business",
    }

    agent = _build_agent()
    response = agent.critique({"ranked_outfits": outfits, "debug_summary": {"daily_context": context}})

    assert response["status"] == "needs_review"
    first_issues = response["ranked_outfits"][0]["critic_issues"]
    assert any("Warmth requirement" in issue for issue in first_issues)
    assert any("open footwear" in issue for issue in first_issues)
    assert any("Formality requirement" in issue for issue in first_issues)

    second_issues = response["ranked_outfits"][1]["critic_issues"]
    assert any("reused" in issue for issue in second_issues)


def test_quality_critic_passes_clean_outfits_without_changes() -> None:
    """Well-aligned outfits should return with no critic issues added."""

    outfits = [
        {
            "items": [
                {
                    "item_id": "top-10",
                    "category": "top",
                    "sub_category": "shirt",
                    "style_tags": ["business", "formal"],
                },
                {
                    "item_id": "bottom-10",
                    "category": "bottom",
                    "sub_category": "trousers",
                    "style_tags": ["business"],
                },
                {
                    "item_id": "shoes-10",
                    "category": "shoes",
                    "sub_category": "oxford",
                    "style_tags": ["formal"],
                },
                {
                    "item_id": "outer-10",
                    "category": "outerwear",
                    "sub_category": "blazer",
                    "style_tags": ["business"],
                },
            ]
        }
    ]

    context = {
        "warmth_requirement": "medium",
        "weather_risk_level": "low",
        "formality_requirement": "business",
    }

    agent = _build_agent()
    response = agent.critique({"ranked_outfits": outfits, "debug_summary": {"daily_context": context}})

    assert response["status"] == "ok"
    assert "critic_issues" not in response["ranked_outfits"][0]
    assert response["ranked_outfits"][0]["items"] == outfits[0]["items"]
