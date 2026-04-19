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

    No-op when ``LANGCHAIN_API_KEY`` is empty — this avoids noisy warnings on
    environments without a LangSmith project (CI, local dev without a key).

    Returns:
        True if tracing was activated, False otherwise.
    """
    api_key = settings.LANGCHAIN_API_KEY.strip()
    if not api_key:
        logger.info("LangSmith tracing disabled (no LANGCHAIN_API_KEY set)")
        os.environ["LANGCHAIN_TRACING_V2"] = "false"
        return False

    os.environ["LANGCHAIN_TRACING_V2"] = "true" if settings.LANGCHAIN_TRACING_V2 else "false"
    os.environ["LANGCHAIN_API_KEY"] = api_key
    os.environ["LANGCHAIN_PROJECT"] = settings.LANGCHAIN_PROJECT

    if settings.LANGCHAIN_TRACING_V2:
        logger.info("LangSmith tracing enabled (project=%s)", settings.LANGCHAIN_PROJECT)
        return True

    logger.info("LangSmith credentials loaded but tracing flag is false")
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
