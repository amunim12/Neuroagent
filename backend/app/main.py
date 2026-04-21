import asyncio
import sys

# psycopg v3 async requires SelectorEventLoop — Windows defaults to ProactorEventLoop.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api.v1.router import api_router
from app.config import settings
from app.db.base import engine
from app.utils.tracing import configure_tracing

# Activate LangSmith tracing before any LangChain/LangGraph imports run downstream.
configure_tracing()

limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Dispose the DB engine on shutdown.

    Schema creation is handled by Alembic migrations — run `alembic upgrade head`
    before starting the server. Test suites set up their own schema in
    tests/conftest.py.
    """
    yield
    await engine.dispose()


app = FastAPI(
    title="NeuroAgent API",
    description="Autonomous AI Agent Backend",
    version="1.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")
