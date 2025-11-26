"""Deprecated calendar compatibility shim.

Prefer importing from :mod:`tools.calendar_provider` instead. This module
re-exports the validated provider interfaces to avoid breaking legacy
imports while guiding callers toward the canonical path.
"""

from warnings import warn

from tools.calendar_provider import (
    CalendarEvent,
    CalendarProvider,
    GoogleCalendarProvider,
    MockCalendarProvider,
)

warn(
    "tools.calendar is deprecated; import from tools.calendar_provider instead.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = [
    "CalendarEvent",
    "CalendarProvider",
    "GoogleCalendarProvider",
    "MockCalendarProvider",
]
