"""Local stub loader for optional google.generativeai dependency.

This project favors local, offline testing. When the `google.generativeai`
package is not installed, this module injects lightweight stand-ins into
``sys.modules`` so that imports used for agent wiring succeed without
network-backed functionality.
"""
from __future__ import annotations

import importlib
import importlib.util
import sys
import types
from typing import Any


def ensure_genai_imports() -> None:
    """Provide stub modules if ``google.generativeai`` is unavailable."""

    def _safe_find_spec(name: str):
        existing = sys.modules.get(name)
        if existing and getattr(existing, "__spec__", None) is not None:
            return existing.__spec__
        try:
            return importlib.util.find_spec(name)
        except ValueError:
            return None

    genai_spec = _safe_find_spec("google.generativeai")
    agent_spec = _safe_find_spec("google.generativeai.agent")

    if genai_spec is None:
        google_module = sys.modules.setdefault("google", types.ModuleType("google"))
        genai_module = sys.modules.setdefault(
            "google.generativeai", types.ModuleType("google.generativeai")
        )
        google_module.generativeai = genai_module
    else:
        genai_module = importlib.import_module("google.generativeai")

    if agent_spec is None:
        agent_module = sys.modules.setdefault(
            "google.generativeai.agent", types.ModuleType("google.generativeai.agent")
        )
    else:
        agent_module = importlib.import_module("google.generativeai.agent")

    def _noop_configure(*_: Any, **__: Any) -> None:
        """No-op replacement for ``genai.configure`` when offline."""

    class _StubTool:
        def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: D401
            """Lightweight placeholder for ADK Tool definitions."""

    class _StubLlmAgent:
        def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: D401
            """Minimal stub to satisfy agent construction locally."""

        def __call__(self, *args: Any, **kwargs: Any) -> dict:
            return {}

    class _StubApp:
        def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: D401
            """Basic stand-in for the ADK App container."""

        def register(self, *args: Any, **kwargs: Any) -> None:
            return None

    if not hasattr(genai_module, "configure"):
        genai_module.configure = _noop_configure
    agent_module.App = getattr(agent_module, "App", _StubApp)
    agent_module.LlmAgent = getattr(agent_module, "LlmAgent", _StubLlmAgent)
    agent_module.Tool = getattr(agent_module, "Tool", _StubTool)


__all__ = ["ensure_genai_imports"]
