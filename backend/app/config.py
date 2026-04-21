import json
from typing import Literal

from pydantic import field_validator, model_validator
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
    DATABASE_URL: str = "postgresql+psycopg://postgres:password@localhost:5432/neuroagent"
    REDIS_URL: str = "redis://localhost:6379/0"
    PINECONE_API_KEY: str = ""
    PINECONE_INDEX_NAME: str = "neuroagent-memory"
    PINECONE_ENVIRONMENT: str = "us-east-1-aws"

    # Auth
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # App — set FRONTEND_URL on Railway to automatically allow that origin
    FRONTEND_URL: str = ""
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:3003",
        "http://localhost:3004",
    ]
    ENVIRONMENT: str = "development"

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

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalize_db_url(cls, v: str) -> str:
        """Rewrite Railway's plain postgresql:// URL to use the psycopg v3 driver."""
        for prefix in ("postgresql://", "postgres://"):
            if v.startswith(prefix):
                return v.replace(prefix, "postgresql+psycopg://", 1)
        return v

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: object) -> list[str]:
        """Accept a JSON array, a comma-separated string, or a plain list.

        Railway env vars are plain strings, so ["url1","url2"] arrives as a
        string rather than a parsed list. This validator handles all formats.
        """
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("["):
                return json.loads(v)
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v  # type: ignore[return-value]

    @model_validator(mode="after")
    def inject_frontend_url(self) -> "Settings":
        """Add FRONTEND_URL to CORS_ORIGINS so only one var needs setting on Railway."""
        if self.FRONTEND_URL and self.FRONTEND_URL not in self.CORS_ORIGINS:
            self.CORS_ORIGINS = [*self.CORS_ORIGINS, self.FRONTEND_URL]
        return self

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
