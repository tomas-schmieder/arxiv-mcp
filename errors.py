"""Sanitize exceptions before they reach an MCP client.

Returning generic messages to callers, and keeping detail in server logs,
follows the OWASP Error Handling Cheat Sheet:
https://cheatsheetseries.owasp.org/cheatsheets/Error_Handling_Cheat_Sheet.html
"""

from __future__ import annotations

import logging

import requests

logger = logging.getLogger("academic-research-mcp")
logger.addHandler(logging.NullHandler())

CLIENT_SEARCH_ERROR = (
    "Paper search is temporarily unavailable. Please try again later."
)


def sanitize_search_error(
    exc: BaseException,
    response: requests.Response | None = None,
) -> str:
    """Log the real failure server-side and return a generic client message."""
    logger.exception("search_papers failed: %s", exc)
    if response is not None:
        logger.error(
            "arXiv responded with status %s: %s",
            getattr(response, "status_code", "?"),
            (getattr(response, "text", "") or "")[:500],
        )
    return CLIENT_SEARCH_ERROR
