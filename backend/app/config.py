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
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    ENVIRONMENT: str = "development"

    # LangSmith
    LANGCHAIN_TRACING_V2: bool = True
    LANGCHAIN_API_KEY: str = ""
    LANGCHAIN_PROJECT: str = "neuroagent"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
