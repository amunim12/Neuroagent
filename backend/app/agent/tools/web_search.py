from langchain.tools import tool

from app.config import settings


@tool
def web_search_tool(query: str) -> str:
    """Search the web for current information. Use for facts, news, documentation, and research.
    Input: a natural language search query.
    Returns: a summary of the top search results with URLs."""
    from tavily import TavilyClient

    client = TavilyClient(api_key=settings.TAVILY_API_KEY)
    response = client.search(query=query, search_depth="advanced", max_results=5, include_answer=True)

    output = f"Quick answer: {response.get('answer', 'N/A')}\n\nSources:\n"
    for result in response["results"]:
        output += f"- [{result['title']}]({result['url']}): {result['content'][:300]}\n"
    return output
