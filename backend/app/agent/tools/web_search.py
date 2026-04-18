import logging

from langchain.tools import tool

from app.config import settings

logger = logging.getLogger(__name__)

MAX_RESULTS = 5
MAX_CONTENT_PREVIEW = 300


@tool
def web_search_tool(query: str) -> str:
    """Search the web for current information. Use for facts, news, documentation, and research.
    Input: a natural language search query.
    Returns: a summary of the top search results with URLs."""
    if not query or not query.strip():
        return "Error: search query cannot be empty."

    from tavily import TavilyClient

    try:
        client = TavilyClient(api_key=settings.TAVILY_API_KEY)
        response = client.search(
            query=query.strip(),
            search_depth="advanced",
            max_results=MAX_RESULTS,
            include_answer=True,
        )
    except Exception as e:
        logger.error("Tavily search failed for query '%s': %s", query, e)
        return f"Web search failed: {e}"

    answer = response.get("answer", "N/A")
    results = response.get("results", [])

    if not results:
        return f"Quick answer: {answer}\n\nNo detailed sources found."

    output = f"Quick answer: {answer}\n\nSources:\n"
    for result in results:
        title = result.get("title", "Untitled")
        url = result.get("url", "")
        content = result.get("content", "")[:MAX_CONTENT_PREVIEW]
        output += f"- [{title}]({url}): {content}\n"

    return output
