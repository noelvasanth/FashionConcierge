"""Root orchestrator agent wiring for Fashion Concierge."""

from typing import Any, Dict

from adk_app.genai_fallback import ensure_genai_imports

ensure_genai_imports()

from google.generativeai import agent as genai_agent

from adk_app.config import ADKConfig
from agents.outfit_stylist_agent import OutfitStylistAgent


class OrchestratorAgent:
    """Plans calls to sub-agents and tools.

    The implementation is intentionally lightweight for the initial scaffold. The
    orchestrator can respond to a simple health-check style message locally while
    still creating an ADK `LlmAgent` that will eventually coordinate the full
    workflow.
    """

    def __init__(
        self, config: ADKConfig, tools: list | None = None, stylist_agent: OutfitStylistAgent | None = None
    ) -> None:
        self.config = config
        self.tools = tools or []
        self.stylist_agent = stylist_agent
        self.system_instruction = (
            "You are the Fashion Concierge orchestrator. Receive user inputs, "
            "plan the next steps across calendar, weather, wardrobe and stylist "
            "agents, and compose a concise response."
        )
        self._llm_agent = self._build_llm_agent()

    def _build_llm_agent(self) -> genai_agent.LlmAgent:
        """Create the ADK LlmAgent instance."""

        return genai_agent.LlmAgent(
            model=self.config.model,
            system_instruction=self.system_instruction,
            name="orchestrator",
            tools=self.tools,
        )

    @property
    def adk_agent(self) -> genai_agent.LlmAgent:
        """Expose the underlying ADK agent for registration on the app."""

        return self._llm_agent

    def handle_message(self, message: str) -> Dict[str, Any]:
        """Provide a deterministic response for local smoke tests."""

        if message.lower().strip() == "hello from fashion concierge":
            return {
                "status": "ok",
                "agent": "orchestrator",
                "message": "Hello from Fashion Concierge! The orchestrator is online.",
            }

        return {
            "status": "unknown",
            "agent": "orchestrator",
            "message": "This is a scaffolded orchestrator. Expand sub-agent calls next.",
        }

    def create_outfit(self, user_id: str, mood: str | None = None) -> Dict[str, Any]:
        """Delegate outfit creation to the stylist agent when available."""

        if not self.stylist_agent:
            return {"status": "error", "message": "Stylist agent not configured."}
        response = self.stylist_agent.recommend_outfit(user_id=user_id, mood=mood)
        return {"status": "ok", "agent": "orchestrator", "outfit": response}
