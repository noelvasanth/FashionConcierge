"""Quality critic agent with rule-based checks and optional LLM review."""

from __future__ import annotations

import logging
from typing import Any, Dict, Iterable, List, Sequence, Tuple

from adk_app.genai_fallback import ensure_genai_imports

ensure_genai_imports()

from google.generativeai import agent as genai_agent

from adk_app.config import ADKConfig
from logic.safety import system_instruction


class QualityCriticAgent:
    """Reviews stylist output for conflicts and repetition.

    The critic performs deterministic checks first to keep behaviour transparent
    and cheap, and can optionally request a lightweight LLM opinion for
    borderline cases.
    """

    def __init__(self, config: ADKConfig) -> None:
        self.config = config
        self.system_instruction = system_instruction(
            "quality critic. Review outfits, flag conflicts, and avoid inventing wardrobe details beyond provided IDs."
        )
        self.logger = logging.getLogger(__name__)
        self._llm_agent = genai_agent.LlmAgent(
            model=self.config.model,
            system_instruction=self.system_instruction,
            name="quality-critic",
            tools=[],
        )

    @property
    def adk_agent(self) -> genai_agent.LlmAgent:
        return self._llm_agent

    def critique(
        self,
        stylist_response: Dict[str, Any] | Sequence[Dict[str, Any]],
        context: Dict[str, Any] | None = None,
        use_llm: bool = False,
    ) -> Dict[str, Any]:
        """Run rule-based quality checks and annotate outfits.

        Args:
            stylist_response: Either the stylist payload containing
                ``ranked_outfits`` (as returned by ``OutfitStylistAgent``) or a
                bare list of outfit dictionaries.
            context: Optional daily context containing warmth, weather risk and
                formality hints. If omitted the method will attempt to pull it
                from ``debug_summary.daily_context`` in the stylist payload.
            use_llm: Whether to request a lightweight LLM verdict for outfits
                that already have rule-based issues.

        Returns:
            A dictionary with ``status`` (``"ok"`` or ``"needs_review"``), the
            reviewed ``ranked_outfits`` (annotated with ``critic_issues`` when
            relevant), and a flattened ``issues`` list for quick inspection.
        """

        outfits, response_context = self._normalise_input(stylist_response)
        context = context or response_context
        reviewed: List[Dict[str, Any]] = []
        aggregated_issues: List[str] = []
        seen_items: set[str] = set()

        for outfit in outfits:
            items: List[Dict[str, Any]] = list(outfit.get("items", []))
            issues: List[str] = []
            issues.extend(self._check_weather(items, context))
            issues.extend(self._check_formality(items, context))

            duplicates = self._detect_repetition(items, seen_items)
            if duplicates:
                issues.append(f"Item(s) reused across outfits: {', '.join(sorted(duplicates))}.")
            seen_items.update({item.get("item_id") for item in items if item.get("item_id")})

            llm_verdict = self._llm_verdict(outfit, issues) if use_llm and issues else None
            updated = dict(outfit)
            if issues:
                updated["critic_issues"] = issues
                aggregated_issues.extend(issues)
            if llm_verdict:
                updated["llm_verdict"] = llm_verdict
            reviewed.append(updated)

        status = "needs_review" if aggregated_issues else "ok"
        return {
            "status": status,
            "ranked_outfits": reviewed,
            "issues": aggregated_issues,
            "context": context,
        }

    def _normalise_input(
        self, stylist_response: Dict[str, Any] | Sequence[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Extract outfits and context from flexible inputs."""

        if isinstance(stylist_response, dict):
            outfits = list(stylist_response.get("ranked_outfits", []))
            context = stylist_response.get("debug_summary", {}).get("daily_context", {})
        else:
            outfits = list(stylist_response)
            context = {}
        return outfits, context

    def _check_weather(self, items: List[Dict[str, Any]], context: Dict[str, Any]) -> List[str]:
        """Flag weather-related issues such as missing outerwear or open shoes."""

        warmth_requirement = str(context.get("warmth_requirement", "medium")).lower()
        weather_risk = str(context.get("weather_risk_level", "low")).lower()
        categories = {str(item.get("category", "")).lower() for item in items}
        sub_categories = {str(item.get("sub_category", "")).lower() for item in items}

        issues: List[str] = []
        if warmth_requirement == "high" and "outerwear" not in categories:
            issues.append("Warmth requirement is high but no outer layer is present.")

        if weather_risk == "high" and sub_categories.intersection({"sandals", "slides", "flip flops", "flip-flops"}):
            issues.append("High weather risk detected but outfit includes open footwear.")

        return issues

    def _check_formality(self, items: List[Dict[str, Any]], context: Dict[str, Any]) -> List[str]:
        """Validate outfits against the required formality level."""

        required = str(context.get("formality_requirement", "informal")).lower()
        style_tags = {tag for item in items for tag in item.get("style_tags", [])}

        if required == "business" and not style_tags.intersection({"business", "formal", "smart"}):
            return ["Formality requirement is business but items lack business or formal styling."]
        if required == "formal" and "formal" not in style_tags:
            return ["Formal occasion flagged yet outfit is missing formal pieces."]
        return []

    def _detect_repetition(
        self, items: Iterable[Dict[str, Any]], seen_items: set[str]
    ) -> List[str]:
        """Identify items that appear across multiple outfits."""

        duplicates: List[str] = []
        for item in items:
            item_id = str(item.get("item_id")) if item.get("item_id") is not None else None
            if item_id and item_id in seen_items:
                duplicates.append(item_id)
        return duplicates

    def _llm_verdict(self, outfit: Dict[str, Any], issues: List[str]) -> str | None:
        """Request a short LLM verdict summarising whether issues are blocking."""

        prompt = (
            "Given the outfit and the rule-based issues, respond with a concise verdict "
            "such as 'revise' or 'minor tweaks' without inventing new wardrobe items."
        )
        try:
            response = self._llm_agent(inputs={"outfit": outfit, "issues": issues}, prompt=prompt)
        except Exception as exc:  # noqa: BLE001
            self.logger.debug("LLM verdict skipped: %s", exc)
            return None

        if isinstance(response, dict):
            if response.get("output"):
                return str(response["output"])
            if response.get("response"):
                return str(response["response"])
        return None
