"""Tools that expose memory services to agents."""

from adk_app.genai_fallback import ensure_genai_imports

ensure_genai_imports()

from google.generativeai import agent as genai_agent

from memory.user_profile import UserMemoryService
from tools.observability import instrument_tool


def user_profile_tool(memory_service: UserMemoryService) -> genai_agent.Tool:
    """Create a tool for fetching user profiles."""

    return genai_agent.Tool(
        name="get_user_profile",
        description="Return the stored user profile for personalization.",
        func=instrument_tool("get_user_profile")(memory_service.get_user_profile),
    )


def update_user_preferences_tool(memory_service: UserMemoryService) -> genai_agent.Tool:
    """Create a tool for persisting user preference updates."""

    return genai_agent.Tool(
        name="update_user_preferences",
        description="Store long-term user preferences to personalize future replies.",
        func=instrument_tool("update_user_preferences")(memory_service.update_user_preferences),
    )


__all__ = ["user_profile_tool", "update_user_preferences_tool"]
