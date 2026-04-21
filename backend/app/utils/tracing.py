"""LangSmith tracing setup.

LangChain / LangGraph read tracing config from environment variables at import
time. Pydantic settings alone are not enough — we must export the values to
``os.environ`` before the graph runs.
"""

import logging
import os

from app.config import settings

logger = logging.getLogger(__name__)


def configure_tracing() -> bool:
    """Export LangSmith environment variables so LangChain enables tracing.

    Accepts both LANGCHAIN_ and LANGSMITH_ prefixed variables so the same
    .env file works regardless of which naming convention was used.

    Returns:
        True if tracing was activated, False otherwise.
    """
    # Resolve API key — prefer LANGSMITH_ prefix (newer convention)
    api_key = (settings.LANGSMITH_API_KEY or settings.LANGCHAIN_API_KEY).strip()
    if not api_key:
        logger.info("LangSmith tracing disabled (no API key set)")
        os.environ["LANGCHAIN_TRACING_V2"] = "false"
        return False

    # Resolve tracing flag — either prefix activates it
    tracing_on = settings.LANGSMITH_TRACING or settings.LANGCHAIN_TRACING_V2

    # Resolve project name
    project = (settings.LANGSMITH_PROJECT or settings.LANGCHAIN_PROJECT or "neuroagent").strip('"')

    os.environ["LANGCHAIN_TRACING_V2"] = "true" if tracing_on else "false"
    os.environ["LANGCHAIN_API_KEY"] = api_key
    os.environ["LANGCHAIN_PROJECT"] = project
    os.environ["LANGCHAIN_ENDPOINT"] = settings.LANGSMITH_ENDPOINT

    if tracing_on:
        logger.info("LangSmith tracing enabled (project=%s)", project)
        return True

    logger.info("LangSmith API key loaded but tracing flag is false")
    return False


def run_config(session_id: str, user_id: str, goal: str) -> dict:
    """Build a LangChain ``RunnableConfig`` for a single agent invocation.

    Attaches metadata + tags so individual runs are filterable in the LangSmith
    dashboard by user and session.
    """
    return {
        "run_name": f"agent-run:{session_id}",
        "tags": ["neuroagent", settings.ENVIRONMENT],
        "metadata": {
            "session_id": session_id,
            "user_id": user_id,
            "goal": goal,
            "environment": settings.ENVIRONMENT,
        },
    }
