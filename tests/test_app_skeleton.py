"""
Phase zero skeleton validation tests for the Fashion Concierge ADK project.
These tests ensure the initial scaffold is wired correctly and will be expanded
in later phases.
"""

from importlib import import_module
from pathlib import Path
from typing import Tuple

import sys
import types

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))


class _DummyTool:
    def __init__(self, *_, **__):
        pass


class _DummyLlmAgent:
    def __init__(self, *_, name: str | None = None, **__):
        self.name = name or "agent"


class _DummyApp:
    def __init__(self, *_, **__):
        self.registry: list = []

    def register(self, component: object) -> None:
        self.registry.append(component)


_google_module = types.ModuleType("google")
_genai_module = types.ModuleType("google.generativeai")
_genai_agent_module = types.ModuleType("google.generativeai.agent")

_genai_agent_module.Tool = _DummyTool
_genai_agent_module.LlmAgent = _DummyLlmAgent
_genai_agent_module.App = _DummyApp

_genai_module.agent = _genai_agent_module
_genai_module.configure = lambda **_: None
_google_module.generativeai = _genai_module

sys.modules.setdefault("google", _google_module)
sys.modules.setdefault("google.generativeai", _genai_module)
sys.modules.setdefault("google.generativeai.agent", _genai_agent_module)

from adk_app import app as app_module
from adk_app.app import FashionConciergeApp
from google.generativeai import agent as genai_agent


@pytest.fixture()
def stubbed_genai_config(monkeypatch: pytest.MonkeyPatch) -> None:
    """Prevent external configuration calls when instantiating the app."""

    monkeypatch.setattr(app_module.genai, "configure", lambda **_: None)


def test_app_factory_creates_app(stubbed_genai_config: None) -> None:
    """App factory returns an ADK App with a fashion concierge orchestrator."""

    app = FashionConciergeApp()
    assert isinstance(app.adk_app, genai_agent.App)
    assert "fashion concierge" in app.orchestrator.system_instruction.lower()


def test_root_agent_responds_to_simple_message(stubbed_genai_config: None) -> None:
    """Root agent handles a ping locally and mentions the project greeting."""

    app = FashionConciergeApp()
    response = app.orchestrator.handle_message("Hello from Fashion Concierge")

    assert isinstance(response, dict)
    message = response.get("message", "")
    assert isinstance(message, str) and message.strip()
    assert "fashion concierge" in message.lower()


@pytest.mark.parametrize(
    "module_path, public_members",
    [
        ("agents.orchestrator", ("OrchestratorAgent",)),
        ("agents.wardrobe_ingestion", ("WardrobeIngestionAgent",)),
        ("agents.wardrobe_query", ("WardrobeQueryAgent",)),
        ("agents.calendar_agent", ("CalendarAgent",)),
        ("agents.weather_agent", ("WeatherAgent",)),
        ("agents.outfit_stylist", ("OutfitStylistAgent",)),
        ("agents.quality_critic", ("QualityCriticAgent",)),
    ],
)
def test_agent_modules_export_expected_members(module_path: str, public_members: Tuple[str, ...]) -> None:
    """Agent modules should import cleanly and expose expected classes."""

    module = import_module(module_path)
    for member in public_members:
        assert hasattr(module, member), f"{module_path} is missing {member}"


@pytest.mark.parametrize(
    "module_path, public_members",
    [
        ("tools.calendar_provider", ("CalendarProvider", "GoogleCalendarProvider")),
        ("tools.weather_provider", ("WeatherProvider", "OpenWeatherProvider")),
        ("tools.wardrobe_store", ("WardrobeStore", "SQLiteWardrobeStore")),
        ("tools.rag", ("WardrobeRAG",)),
        ("tools.memory_tools", ("user_profile_tool",)),
        ("tools.session_tools", ("session_toolkit",)),
    ],
)
def test_tool_modules_export_expected_members(module_path: str, public_members: Tuple[str, ...]) -> None:
    """Tool modules should import cleanly and expose expected members."""

    module = import_module(module_path)
    for member in public_members:
        assert hasattr(module, member), f"{module_path} is missing {member}"
