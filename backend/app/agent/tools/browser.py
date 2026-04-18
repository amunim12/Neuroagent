import asyncio
import json

from langchain.tools import tool


@tool
def browser_tool(action: str) -> str:
    """Control a web browser to navigate URLs, scrape content, fill forms, or click elements.
    Input: JSON with keys: action (navigate|scrape|click|fill), url, selector, value.
    Returns: page content or action result."""
    try:
        params = json.loads(action)
        return asyncio.run(_browser_action(params))
    except json.JSONDecodeError:
        return "Invalid JSON input. Expected keys: action, url, selector (optional), value (optional)."
    except Exception as e:
        return f"Browser action failed: {e}"


async def _browser_action(params: dict) -> str:
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            action = params.get("action", "navigate")
            url = params.get("url", "")

            if action == "navigate":
                await page.goto(url, wait_until="networkidle")
                return f"Navigated to {url}. Title: {await page.title()}"

            if action == "scrape":
                await page.goto(url, wait_until="networkidle")
                content = await page.inner_text("body")
                return content[:3000]

            if action == "click":
                await page.goto(url)
                await page.click(params["selector"])
                return f"Clicked element: {params['selector']}"

            if action == "fill":
                await page.goto(url)
                await page.fill(params["selector"], params["value"])
                return f"Filled {params['selector']} with value"

            return f"Unknown action: {action}"
        finally:
            await browser.close()
