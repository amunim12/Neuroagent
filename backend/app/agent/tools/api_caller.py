import json

import httpx
from langchain.tools import tool


@tool
def api_caller_tool(request: str) -> str:
    """Make HTTP requests to external REST APIs.
    Input: JSON string with keys: 'method' (GET|POST|PUT|DELETE), 'url', 'headers' (optional dict),
    'body' (optional dict for POST/PUT).
    Returns: API response status and body."""
    try:
        params = json.loads(request)
        with httpx.Client(timeout=30) as client:
            response = client.request(
                method=params["method"].upper(),
                url=params["url"],
                headers=params.get("headers", {}),
                json=params.get("body"),
            )
            return f"Status: {response.status_code}\nResponse: {response.text[:2000]}"
    except json.JSONDecodeError:
        return "Invalid JSON input. Expected keys: method, url, headers (optional), body (optional)."
    except Exception as e:
        return f"API call failed: {e}"
