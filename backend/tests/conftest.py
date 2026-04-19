"""Shared pytest fixtures.

Each test gets its own SQLite database file in a temporary directory, with
its own async engine and session factory. This kills every class of
cross-test state leakage we have seen in CI:

- In-memory ``:memory:`` + ``StaticPool`` breaks under pytest-asyncio's
  per-test event loops — the cached connection binds to the first loop and
  later tests silently talk to a different DB instance.
- A shared file DB leaves rows behind if an autouse teardown fixture fails
  to run (which ``pytest-asyncio`` will not do around sync tests).

With one file per test, there is simply nothing to leak.
"""

import asyncio
from collections.abc import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base, get_async_session
from app.main import app


def _make_engine(db_path) -> tuple:
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}", echo=False)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    return engine, factory


async def _create_schema(engine) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@pytest.fixture
async def test_db(tmp_path):
    """Per-test engine + session factory backed by a unique SQLite file.

    Registers a dependency override on ``get_async_session`` so FastAPI routes
    pick up this test's database, and tears it down cleanly afterward.
    """
    db_path = tmp_path / "test.db"
    engine, factory = _make_engine(db_path)
    await _create_schema(engine)

    async def override() -> AsyncGenerator[AsyncSession, None]:
        async with factory() as session:
            yield session

    app.dependency_overrides[get_async_session] = override
    try:
        yield factory
    finally:
        app.dependency_overrides.pop(get_async_session, None)
        await engine.dispose()


@pytest.fixture
async def client(test_db) -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def sync_test_db(tmp_path) -> Generator:
    """Per-test engine for sync TestClient-based tests.

    pytest-asyncio's async fixtures don't run around sync tests, so we drive
    the engine setup/teardown through ``asyncio.run`` instead. Returns the
    session factory so callers can patch it into modules that grab
    ``async_session_factory`` directly at import time.
    """
    db_path = tmp_path / "test.db"
    engine, factory = _make_engine(db_path)
    asyncio.run(_create_schema(engine))

    async def override() -> AsyncGenerator[AsyncSession, None]:
        async with factory() as session:
            yield session

    app.dependency_overrides[get_async_session] = override
    try:
        yield factory
    finally:
        app.dependency_overrides.pop(get_async_session, None)
        asyncio.run(engine.dispose())


@pytest.fixture
def sync_client(sync_test_db) -> Generator[TestClient, None, None]:
    """Sync TestClient wired to a per-test database.

    Does not enter TestClient's ``with`` block so the production ``lifespan``
    does not try to dispose the real app engine. The agent endpoint and
    dependency module grab ``async_session_factory`` directly at import time,
    so we patch both references to point at the per-test factory.
    """
    from unittest.mock import patch

    with (
        patch("app.api.v1.agent.async_session_factory", sync_test_db),
        patch("app.dependencies.async_session_factory", sync_test_db),
    ):
        yield TestClient(app)
