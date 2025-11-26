"""Tools for fetching product pages from retailer URLs."""

from __future__ import annotations

import logging
from typing import Optional
from urllib.parse import urlparse

import requests

from adk_app.genai_fallback import ensure_genai_imports

ensure_genai_imports()

from google.generativeai import agent as genai_agent
from tools.observability import instrument_tool

logger = logging.getLogger(__name__)


class InvalidProductURLError(ValueError):
    """Raised when the provided URL is not a valid HTTP or HTTPS URL."""


class ProductPageFetchError(RuntimeError):
    """Raised when the product page cannot be retrieved successfully."""


def _validate_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise InvalidProductURLError(f"Unsupported or invalid URL: {url}")


@instrument_tool("fetch_product_page")
def fetch_product_page(url: str, timeout: Optional[float] = 10.0) -> str:
    """Fetch the raw HTML for a retailer product page.

    Args:
        url: HTTP or HTTPS URL pointing to a retailer product page.
        timeout: Optional network timeout in seconds.

    Returns:
        The HTML content of the page as text.

    Raises:
        InvalidProductURLError: If the URL is not HTTP/HTTPS or missing a host.
        ProductPageFetchError: For network issues or non-2xx responses.
    """

    _validate_url(url)
    logger.info("Fetching product page", extra={"url": url})
    try:
        response = requests.get(url, timeout=timeout)
    except requests.RequestException as exc:  # pragma: no cover - requests base error
        logger.error("Network error fetching product page", extra={"url": url, "error": str(exc)})
        raise ProductPageFetchError(f"Network error fetching {url}: {exc}") from exc

    if not 200 <= response.status_code < 300:
        logger.warning(
            "Non-success status when fetching product page",
            extra={"url": url, "status_code": response.status_code},
        )
        raise ProductPageFetchError(
            f"Failed to fetch {url}: HTTP {response.status_code}"
        )

    logger.debug(
        "Fetched product page successfully",
        extra={"url": url, "status_code": response.status_code, "length": len(response.text)},
    )
    return response.text


def fetch_product_page_tool() -> genai_agent.Tool:
    """Expose :func:`fetch_product_page` as an ADK tool."""

    return genai_agent.Tool(
        name="fetch_product_page",
        description="Fetch the raw HTML of a retailer product page given its URL.",
        func=fetch_product_page,
    )


__all__ = [
    "InvalidProductURLError",
    "ProductPageFetchError",
    "fetch_product_page",
    "fetch_product_page_tool",
]
