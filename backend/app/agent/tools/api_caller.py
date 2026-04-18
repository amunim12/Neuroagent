import json
import logging

import httpx
from langchain.tools import tool

logger = logging.getLogger(__name__)

MAX_RESPONSE_LENGTH = 2000
REQUEST_TIMEOUT = 30
VALID_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}


@tool
def api_caller_tool(request: str) -> str:
    """Make HTTP requests to external REST APIs.
    Input: JSON string with keys: 'method' (GET|POST|PUT|DELETE), 'url',
    'headers' (optional dict), 'body' (optional dict for POST/PUT).
    Returns: API response status and body."""
    try:
        params = json.loads(request)
    except json.JSONDecodeError:
        return "Invalid JSON input. Expected: {\"method\": \"GET\", \"url\": \"...\"}."

    method = params.get("method", "").upper()
    if method not in VALID_METHODS:
        return f"Invalid HTTP method '{method}'. Valid methods: {', '.join(sorted(VALID_METHODS))}."

    url = params.get("url", "")
    if not url:
        return "Error: 'url' is required."

    try:
        with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
            response = client.request(
                method=method,
                url=url,
                headers=params.get("headers", {}),
                json=params.get("body"),
            )
            body = response.text[:MAX_RESPONSE_LENGTH]
            if len(response.text) > MAX_RESPONSE_LENGTH:
                body += f"\n\n... (truncated, {len(response.text)} total chars)"
            return f"Status: {response.status_code}\nResponse:\n{body}"
    except httpx.TimeoutException:
        return f"Request timed out after {REQUEST_TIMEOUT}s for {url}."
    except Exception as e:
        logger.error("API call to %s failed: %s", url, e)
        return f"API call failed: {e}"
