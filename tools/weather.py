"""Deprecated weather compatibility shim.

Callers should import from :mod:`tools.weather_provider` going forward. The
validated provider interfaces remain available here for backwards
compatibility while documentation migrates fully to the canonical module.
"""

from warnings import warn

from tools.weather_provider import (
    MockWeatherProvider,
    OpenWeatherProvider,
    WeatherProfile,
    WeatherProvider,
)

warn(
    "tools.weather is deprecated; import from tools.weather_provider instead.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = [
    "WeatherProfile",
    "WeatherProvider",
    "OpenWeatherProvider",
    "MockWeatherProvider",
]
