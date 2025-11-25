"""Root orchestrator agent wiring for Fashion Concierge."""

from typing import Any, Dict

from adk_app.genai_fallback import ensure_genai_imports

ensure_genai_imports()

from google.generativeai import agent as genai_agent

from adk_app.config import ADKConfig


class OrchestratorAgent:
    """Plans calls to sub-agents and tools.

    The implementation is intentionally lightweight for the initial scaffold. The
    orchestrator can respond to a simple health-check style message locally while
    still creating an ADK `LlmAgent` that will eventually coordinate the full
    workflow.
    """

    def __init__(self, config: ADKConfig, tools: list | None = None) -> None:
        self.config = config
        self.tools = tools or []
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
