"""Structured logging and tracing helpers for the Fashion Concierge app."""

from __future__ import annotations

import contextlib
import contextvars
import importlib
import importlib.util
import json
import logging
import os
import uuid
from typing import Any, Dict, Iterator

CORRELATION_ID = contextvars.ContextVar("correlation_id", default=None)
_DEFAULT_EXCLUDE_KEYS = {
    "name",
    "msg",
    "args",
    "levelname",
    "levelno",
    "pathname",
    "filename",
    "module",
    "exc_info",
    "exc_text",
    "stack_info",
    "lineno",
    "funcName",
    "created",
    "msecs",
    "relativeCreated",
    "thread",
    "threadName",
    "processName",
    "process",
    "message",
}

_TRACING_MODULE: object | bool | None = None


class JsonFormatter(logging.Formatter):
    """Emit structured JSON logs with correlation metadata."""

    def format(self, record: logging.LogRecord) -> str:  # noqa: D401
        record_message = super().format(record)
        correlation_id = getattr(record, "correlation_id", None) or CORRELATION_ID.get()
        payload: Dict[str, Any] = {
            "timestamp": self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record_message,
            "event": getattr(record, "event", record_message),
            "correlation_id": correlation_id,
        }

        for key, value in record.__dict__.items():
            if key in _DEFAULT_EXCLUDE_KEYS or key in payload:
                continue
            payload[key] = value
        return json.dumps(payload)


def configure_logging(level: int | str | None = None) -> None:
    """Configure root logging with JSON output."""

    desired_level = level or os.getenv("LOG_LEVEL", "INFO")
    logging.root.handlers.clear()
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logging.basicConfig(level=desired_level, handlers=[handler])


def get_logger(name: str) -> logging.Logger:
    """Return a module logger ensuring configuration is applied."""

    if not logging.getLogger().handlers:
        configure_logging()
    return logging.getLogger(name)


def ensure_correlation_id(correlation_id: str | None = None) -> str:
    """Return an existing correlation id or assign a new one."""

    current = CORRELATION_ID.get()
    if correlation_id:
        CORRELATION_ID.set(correlation_id)
        return correlation_id
    if current:
        return current
    new_id = uuid.uuid4().hex
    CORRELATION_ID.set(new_id)
    return new_id


@contextlib.contextmanager
def correlation_context(correlation_id: str | None = None) -> Iterator[str]:
    """Context manager to temporarily set a correlation id."""

    token = CORRELATION_ID.set(correlation_id or ensure_correlation_id())
    try:
        yield CORRELATION_ID.get()
    finally:
        CORRELATION_ID.reset(token)


def _load_tracing_module() -> object | None:
    global _TRACING_MODULE
    if _TRACING_MODULE is None:
        try:
            spec = importlib.util.find_spec("google.generativeai.tracing")
        except (ModuleNotFoundError, AttributeError):
            _TRACING_MODULE = False
            return None
        if spec:
            try:
                _TRACING_MODULE = importlib.import_module("google.generativeai.tracing")
            except ModuleNotFoundError:
                _TRACING_MODULE = False
        else:
            _TRACING_MODULE = False
    return _TRACING_MODULE if _TRACING_MODULE else None


@contextlib.contextmanager
def tracing_span(name: str, **attributes: Any) -> Iterator[object | None]:
    """Return a tracing span context if ADK tracing is installed."""

    tracer = _load_tracing_module()
    if tracer is None:
        yield None
        return

    if hasattr(tracer, "Span"):
        with tracer.Span(name=name, attributes=attributes) as span:  # type: ignore[attr-defined]
            yield span
        return

    if hasattr(tracer, "start_span"):
        span = tracer.start_span(name=name, attributes=attributes)  # type: ignore[attr-defined]
        try:
            yield span
        finally:
            if hasattr(span, "end"):
                span.end()
        return

    yield None


def log_event(logger: logging.Logger, level: int, event: str, **fields: Any) -> None:
    """Emit a structured log entry with correlation metadata."""

    correlation_id = ensure_correlation_id(fields.pop("correlation_id", None))
    exc_info = fields.pop("exc_info", None)
    logger.log(level, event, exc_info=exc_info, extra={"event": event, "correlation_id": correlation_id, **fields})


@contextlib.contextmanager
def operation_context(name: str, **attributes: Any) -> Iterator[str]:
    """Combine correlation id scoping with tracing spans."""

    correlation_id = ensure_correlation_id(attributes.get("correlation_id"))
    with correlation_context(correlation_id) as scoped_id, tracing_span(name, **attributes):
        yield scoped_id


__all__ = [
    "configure_logging",
    "correlation_context",
    "ensure_correlation_id",
    "get_logger",
    "log_event",
    "operation_context",
    "tracing_span",
]
