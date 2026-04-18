import asyncio
import json
import logging

from langchain.tools import tool

logger = logging.getLogger(__name__)

MAX_SCRAPE_LENGTH = 3000
PAGE_TIMEOUT_MS = 15000
VALID_ACTIONS = {"navigate", "scrape", "click", "fill"}


@tool
def browser_tool(action: str) -> str:
    """Control a web browser to navigate URLs, scrape content, fill forms, or click elements.
    Input: JSON with keys: action (navigate|scrape|click|fill), url, selector, value.
    Returns: page content or action result."""
    try:
        params = json.loads(action)
    except json.JSONDecodeError:
        return "Invalid JSON input. Expected: {\"action\": \"...\", \"url\": \"...\"}."

    action_type = params.get("action", "navigate")
    if action_type not in VALID_ACTIONS:
        return f"Unknown action '{action_type}'. Valid actions: {', '.join(sorted(VALID_ACTIONS))}."

    url = params.get("url", "")
    if not url:
        return "Error: 'url' is required."

    # Validate required fields for specific actions before launching a browser
    if action_type == "click" and not params.get("selector"):
        return "Error: 'selector' is required for click action."
    if action_type == "fill" and (not params.get("selector") or not params.get("value")):
        return "Error: 'selector' and 'value' are required for fill action."

    # Use an existing event loop if available, otherwise create one
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    try:
        if loop and loop.is_running():
            # Running inside an async context (e.g., FastAPI) -- use a new thread
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as pool:
                result = pool.submit(asyncio.run, _browser_action(params)).result(timeout=30)
            return result
        return asyncio.run(_browser_action(params))
    except Exception as e:
        logger.error("Browser action failed: %s", e)
        return f"Browser action failed: {e}"


async def _browser_action(params: dict) -> str:
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        page.set_default_timeout(PAGE_TIMEOUT_MS)
        try:
            action = params["action"]
            url = params["url"]

            if action == "navigate":
                await page.goto(url, wait_until="networkidle")
                title = await page.title()
                return f"Navigated to {url}. Title: {title}"

            if action == "scrape":
                await page.goto(url, wait_until="networkidle")
                content = await page.inner_text("body")
                truncated = content[:MAX_SCRAPE_LENGTH]
                if len(content) > MAX_SCRAPE_LENGTH:
                    truncated += f"\n\n... (truncated, {len(content)} total chars)"
                return truncated

            if action == "click":
                selector = params.get("selector", "")
                if not selector:
                    return "Error: 'selector' is required for click action."
                await page.goto(url)
                await page.click(selector)
                return f"Clicked element: {selector}"

            if action == "fill":
                selector = params.get("selector", "")
                value = params.get("value", "")
                if not selector or not value:
                    return "Error: 'selector' and 'value' are required for fill action."
                await page.goto(url)
                await page.fill(selector, value)
                return f"Filled {selector} with value"

            return f"Unknown action: {action}"
        finally:
            await browser.close()
