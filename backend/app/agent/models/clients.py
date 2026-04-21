import logging

from langchain_anthropic import ChatAnthropic
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI

from app.config import settings

logger = logging.getLogger(__name__)

MODEL_GPT4O = "gpt-4o"
MODEL_CLAUDE_SONNET = "claude-sonnet"
MODEL_GROQ_LLAMA3 = "groq-llama3"

# Fallback chain: try each model in order until one succeeds.
# Groq free tier has daily/per-minute limits; Claude is the paid fallback.
_FALLBACK_CHAIN = [MODEL_GROQ_LLAMA3, MODEL_CLAUDE_SONNET, MODEL_GPT4O]


def _build_llm(model_name: str, streaming: bool):
    if model_name == MODEL_GPT4O:
        return ChatOpenAI(
            model="gpt-4o",
            temperature=0,
            streaming=streaming,
            api_key=settings.OPENAI_API_KEY,
        )
    if model_name == MODEL_CLAUDE_SONNET:
        return ChatAnthropic(
            model="claude-sonnet-4-5-20250514",
            temperature=0,
            streaming=streaming,
            api_key=settings.ANTHROPIC_API_KEY,
        )
    if model_name == MODEL_GROQ_LLAMA3:
        return ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0,
            streaming=streaming,
            api_key=settings.GROQ_API_KEY,
        )
    raise ValueError(f"Unknown model: {model_name}")


def get_llm(model_name: str, streaming: bool = True):
    """Return the LLM client, falling back down the chain on rate-limit errors."""
    chain = _FALLBACK_CHAIN if model_name == MODEL_GROQ_LLAMA3 else [model_name]
    last_err: Exception | None = None
    for candidate in chain:
        try:
            llm = _build_llm(candidate, streaming)
            if candidate != model_name:
                logger.warning("Model %s unavailable, using %s instead", model_name, candidate)
            return llm
        except Exception as exc:  # noqa: BLE001
            # Only swallow config/quota errors; re-raise unexpected ones after chain exhausted.
            last_err = exc
    raise RuntimeError(f"All models in fallback chain failed. Last error: {last_err}")
