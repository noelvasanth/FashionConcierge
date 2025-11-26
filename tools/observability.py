"""Observability helpers for instrumenting tool calls."""

from __future__ import annotations

import logging
import time
from functools import wraps
from typing import Callable, ParamSpec, TypeVar

from adk_app.logging_config import ensure_correlation_id, get_logger, log_event, tracing_span

LOGGER = get_logger(__name__)
P = ParamSpec("P")
R = TypeVar("R")


def _preview_kwargs(kwargs: dict, max_keys: int = 6) -> dict:
    preview: dict = {}
    for idx, (key, value) in enumerate(kwargs.items()):
        if idx >= max_keys:
            preview["truncated"] = True
            break
        preview[key] = value
    return preview


def instrument_tool(tool_name: str) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Wrap a callable to emit structured logs and optional trace spans."""

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            correlation_id = ensure_correlation_id()
            start = time.perf_counter()
            log_event(
                LOGGER,
                logging.INFO,
                "tool_call_started",
                tool=tool_name,
                correlation_id=correlation_id,
                kwargs=_preview_kwargs(kwargs),
            )
            with tracing_span(f"tool:{tool_name}", correlation_id=correlation_id, kind="tool"):
                try:
                    result = func(*args, **kwargs)
                except Exception:
                    duration_ms = round((time.perf_counter() - start) * 1000, 2)
                    log_event(
                        LOGGER,
                        logging.ERROR,
                        "tool_call_failed",
                        tool=tool_name,
                        correlation_id=correlation_id,
                        duration_ms=duration_ms,
                        exc_info=True,
                    )
                    raise
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            log_event(
                LOGGER,
                logging.INFO,
                "tool_call_completed",
                tool=tool_name,
                correlation_id=correlation_id,
                duration_ms=duration_ms,
            )
            return result

        return wrapper

    return decorator


__all__ = ["instrument_tool"]
