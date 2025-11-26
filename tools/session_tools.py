"""Tools exposing session history and events to agents."""
from adk_app.genai_fallback import ensure_genai_imports

ensure_genai_imports()

from google.generativeai import agent as genai_agent

from memory.session_store import SessionManager


def session_history_tool(session_manager: SessionManager) -> genai_agent.Tool:
    return genai_agent.Tool(
        name="get_session_context",
        description="Return recent turns, events, and any running summary for a session.",
        func=session_manager.get_context,
    )


def record_session_turn_tool(session_manager: SessionManager) -> genai_agent.Tool:
    return genai_agent.Tool(
        name="record_session_turn",
        description="Persist a conversational turn for auditing and memory.",
        func=session_manager.record_turn,
    )


def record_session_event_tool(session_manager: SessionManager) -> genai_agent.Tool:
    return genai_agent.Tool(
        name="record_session_event",
        description="Record an event such as schedule, weather, or outfit decisions in the session log.",
        func=session_manager.record_event,
    )


def summarize_session_tool(session_manager: SessionManager) -> genai_agent.Tool:
    return genai_agent.Tool(
        name="summarize_session_history",
        description="Summarize a long conversation into a compact memory blob.",
        func=session_manager.summarize_session,
    )


def session_toolkit(session_manager: SessionManager) -> list:
    return [
        session_history_tool(session_manager),
        record_session_turn_tool(session_manager),
        record_session_event_tool(session_manager),
        summarize_session_tool(session_manager),
    ]


__all__ = [
    "session_toolkit",
    "session_history_tool",
    "record_session_turn_tool",
    "record_session_event_tool",
    "summarize_session_tool",
]
