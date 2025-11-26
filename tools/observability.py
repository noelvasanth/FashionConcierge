"""Observability helpers for instrumenting tool calls."""

from __future__ import annotations

import logging
import time
from functools import wraps
from typing import Callable, ParamSpec, TypeVar

from pydantic import BaseModel, ValidationError

from adk_app.logging_config import (
    ensure_correlation_id,
    get_logger,
    log_event,
    redact_for_log,
    tracing_span,
)

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
    return redact_for_log(preview)


def instrument_tool(
    tool_name: str,
    input_model: type[BaseModel] | None = None,
    on_validation_error: Callable[[ValidationError], R] | None = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Wrap a callable to emit structured logs, validation, and optional trace spans."""

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            correlation_id = ensure_correlation_id()
            start = time.perf_counter()

            if input_model:
                try:
                    validated = input_model.model_validate(kwargs)
                    kwargs = validated.model_dump()
                except ValidationError as exc:  # pragma: no cover - defensive path
                    log_event(
                        LOGGER,
                        logging.WARNING,
                        "tool_validation_failed",
                        tool=tool_name,
                        correlation_id=correlation_id,
                        errors=redact_for_log(exc.errors()),
                    )
                    if on_validation_error:
                        return on_validation_error(exc)
                    raise

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
