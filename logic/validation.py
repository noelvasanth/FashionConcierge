"""Pydantic schemas and helpers for validating agent IO and tool payloads."""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, ValidationError, field_validator


class ToolEnvelope(BaseModel):
    """Generic tool call envelope to enforce safe payload shapes."""

    tool: str
    kwargs: Dict[str, Any]


class CalendarToolInput(BaseModel):
    """Input contract for calendar lookups."""

    user_id: str = Field(min_length=1)
    start_date: date
    end_date: date

    @field_validator("end_date")
    @classmethod
    def _validate_range(cls, end_date: date, values: Dict[str, Any]) -> date:
        start_date = values.get("start_date")
        if start_date and end_date < start_date:
            raise ValueError("end_date cannot precede start_date")
        return end_date


class WeatherToolInput(BaseModel):
    """Input contract for forecast lookups."""

    user_id: str | None = None
    location: str = Field(min_length=1)
    date: date


class OutfitRequest(BaseModel):
    """Shared envelope for orchestrator-driven outfit planning."""

    user_id: str = Field(min_length=1)
    date: date
    location: str = Field(min_length=1)
    mood: str = Field(min_length=2)


class OutfitResponse(BaseModel):
    """Minimal structure expected from orchestrator responses."""

    status: Literal["ok", "error", "needs_review"]
    request: OutfitRequest
    context: Dict[str, Any]
    top_outfits: List[Any] = []
    user_facing_summary: Optional[str] = None
    debug_summary: Optional[Dict[str, Any]] = None


class ValidationResult(BaseModel):
    """Wrapper returned to agents when validation fails."""

    status: Literal["needs_review"] = "needs_review"
    message: str
    details: List[Dict[str, Any]]


def validation_failure(message: str, exc: ValidationError) -> Dict[str, Any]:
    """Translate Pydantic errors into a consistent review payload."""

    return ValidationResult(message=message, details=exc.errors()).model_dump()


__all__ = [
    "ToolEnvelope",
    "CalendarToolInput",
    "WeatherToolInput",
    "OutfitRequest",
    "OutfitResponse",
    "ValidationResult",
    "validation_failure",
]
