"""Quality critic agent stub."""

from typing import List

from adk_app.genai_fallback import ensure_genai_imports

ensure_genai_imports()

from google.generativeai import agent as genai_agent

from adk_app.config import ADKConfig


class QualityCriticAgent:
    """Reviews stylist output for conflicts and repetition."""

    def __init__(self, config: ADKConfig) -> None:
        self.config = config
        self.system_instruction = (
            "You review outfits, flag conflicts like weather mismatches and suggest refinements."
        )
        self._llm_agent = genai_agent.LlmAgent(
            model=self.config.model,
            system_instruction=self.system_instruction,
            name="quality-critic",
            tools=[],
        )

    @property
    def adk_agent(self) -> genai_agent.LlmAgent:
        return self._llm_agent

    def critique(self, outfits: List[dict]) -> List[dict]:
        """Return the outfits untouched for now."""

        return outfits
