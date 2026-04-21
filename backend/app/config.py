from typing import Literal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    # LLM Providers
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    GROQ_API_KEY: str = ""

    # Agent Tools
    TAVILY_API_KEY: str = ""
    E2B_API_KEY: str = ""

    # Databases
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/neuroagent"
    REDIS_URL: str = "redis://localhost:6379/0"
    PINECONE_API_KEY: str = ""
    PINECONE_INDEX_NAME: str = "neuroagent-memory"
    PINECONE_ENVIRONMENT: str = "us-east-1-aws"

    # Auth
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # App
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:3003",
        "http://localhost:3004",
    ]
    ENVIRONMENT: str = "development"

    # Default model for planner, synthesizer, and the router's ambiguous-task
    # fallback. Override via env to steer the agent away from a provider
    # whose quota is exhausted without rewriting the routing heuristics.
    # Free-tier options run through Groq; the OpenAI and Anthropic entries
    # are only viable if you supply a paid API key with remaining quota.
    DEFAULT_AGENT_MODEL: Literal[
        "groq-llama3", "gpt-4o", "claude-sonnet"
    ] = "groq-llama3"

    # LangSmith — .env may use either LANGCHAIN_ or LANGSMITH_ prefix
    LANGCHAIN_TRACING_V2: bool = False
    LANGCHAIN_API_KEY: str = ""
    LANGCHAIN_PROJECT: str = "neuroagent"
    LANGSMITH_TRACING: bool = False
    LANGSMITH_API_KEY: str = ""
    LANGSMITH_PROJECT: str = ""
    LANGSMITH_ENDPOINT: str = "https://api.smith.langchain.com"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
