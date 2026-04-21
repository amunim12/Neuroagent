import logging

import httpx
from langchain.tools import tool

logger = logging.getLogger(__name__)

MAX_RESPONSE_LENGTH = 2000
REQUEST_TIMEOUT = 30
VALID_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}


@tool
def api_caller_tool(
    method: str,
    url: str,
    headers: dict | None = None,
    body: dict | None = None,
) -> str:
    """Make HTTP requests to external REST APIs.

    Args:
        method: HTTP method (GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS).
        url: Full URL to request.
        headers: Optional HTTP headers as a flat dict of strings.
        body: Optional JSON body for POST/PUT/PATCH requests.

    Returns: API response status and body.
    """
    method_upper = (method or "").upper()
    if method_upper not in VALID_METHODS:
        return f"Invalid HTTP method '{method}'. Valid methods: {', '.join(sorted(VALID_METHODS))}."

    if not url:
        return "Error: 'url' is required."

    try:
        with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
            response = client.request(
                method=method_upper,
                url=url,
                headers=headers or {},
                json=body,
            )
            body_text = response.text[:MAX_RESPONSE_LENGTH]
            if len(response.text) > MAX_RESPONSE_LENGTH:
                body_text += f"\n\n... (truncated, {len(response.text)} total chars)"
            return f"Status: {response.status_code}\nResponse:\n{body_text}"
    except httpx.TimeoutException:
        return f"Request timed out after {REQUEST_TIMEOUT}s for {url}."
    except Exception as e:
        logger.error("API call to %s failed: %s", url, e)
        return f"API call failed: {e}"
