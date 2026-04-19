"""Shared pytest fixtures.

Tests use an in-memory SQLite database with ``StaticPool`` so every connection
sees the same schema and rows, but no state leaks to disk or between runs.
The previous file-backed ``./test.db`` caused cross-process contamination in CI
and was occasionally checked in by accident.
"""

import asyncio
from collections.abc import AsyncGenerator, Generator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.db.base import Base, get_async_session
from app.main import app

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# StaticPool keeps a single connection open so every session shares the same
# in-memory database. check_same_thread=False lets TestClient's portal thread
# reuse the connection created on the asyncio thread.
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False,
)
test_session_factory = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


async def _reset_schema() -> None:
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


@pytest.fixture(autouse=True)
async def setup_database() -> AsyncGenerator[None, None]:
    """Reset the schema before every async test.

    Sync tests go through :func:`sync_client_db_reset` instead, since
    pytest-asyncio does not run async autouse fixtures around sync tests.
    """
    await _reset_schema()
    yield


@pytest.fixture
def sync_client_db_reset() -> Generator[None, None, None]:
    """Reset the schema for sync tests that don't trigger the async autouse fixture."""
    asyncio.new_event_loop().run_until_complete(_reset_schema())
    yield


async def override_get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with test_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


app.dependency_overrides[get_async_session] = override_get_async_session


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
