from langchain_anthropic import ChatAnthropic
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI

from app.config import settings

# Model identifiers used throughout the agent graph
MODEL_GPT4O = "gpt-4o"
MODEL_CLAUDE_SONNET = "claude-sonnet"
MODEL_GROQ_LLAMA3 = "groq-llama3"


def get_llm(model_name: str, streaming: bool = True):
    """Return the LLM client for the given model identifier."""
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
            model="llama3-70b-8192",
            temperature=0,
            streaming=streaming,
            api_key=settings.GROQ_API_KEY,
        )
    raise ValueError(f"Unknown model: {model_name}")
