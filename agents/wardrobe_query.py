"""Wardrobe query agent stub."""

from typing import Dict, List

from adk_app.genai_fallback import ensure_genai_imports

ensure_genai_imports()

from google.generativeai import agent as genai_agent

from adk_app.config import ADKConfig
from logic.safety import system_instruction


class WardrobeQueryAgent:
    """Retrieves and filters wardrobe items for an event."""

    def __init__(self, config: ADKConfig, tools: list | None = None) -> None:
        self.config = config
        self.tools = tools or []
        self.system_instruction = system_instruction(
            "wardrobe query agent. Use registered wardrobe tools, apply filters, and keep wardrobe URLs redacted."
        )
        self._llm_agent = genai_agent.LlmAgent(
            model=self.config.model,
            system_instruction=self.system_instruction,
            name="wardrobe-query",
            tools=self.tools,
        )

    @property
    def adk_agent(self) -> genai_agent.LlmAgent:
        return self._llm_agent

    def query(self, event_profile: Dict[str, str], user_id: str) -> List[str]:
        """Return placeholder wardrobe item ids."""

        return [f"sample-item-{user_id}"]
