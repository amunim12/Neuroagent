"""Tests for the agent WebSocket and REST endpoints."""

import uuid
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app
from tests.conftest import test_session_factory

TEST_USER = {"email": "agent-user@example.com", "password": "securepassword123"}


# === REST fallback ===


@pytest.mark.asyncio
async def test_run_agent_requires_auth(client: AsyncClient):
    response = await client.post("/api/v1/agent/run", json={"goal": "Do something"})
    # FastAPI < 0.118 returns 403 for missing HTTPBearer credentials; newer
    # versions return 401. Accept both so the suite works across the pinned range.
    assert response.status_code in {401, 403}


@pytest.mark.asyncio
async def test_run_agent_returns_session_id(client: AsyncClient):
    register = await client.post("/api/v1/auth/register", json=TEST_USER)
    token = register.json()["access_token"]

    response = await client.post(
        "/api/v1/agent/run",
        json={"goal": "Research the Eiffel Tower"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 202
    data = response.json()
    assert "session_id" in data
    assert data["status"] == "running"
    uuid.UUID(data["session_id"])


@pytest.mark.asyncio
async def test_run_agent_rejects_empty_goal(client: AsyncClient):
    register = await client.post("/api/v1/auth/register", json=TEST_USER)
    token = register.json()["access_token"]

    response = await client.post(
        "/api/v1/agent/run",
        json={"goal": ""},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 422


# === WebSocket ===


@pytest.fixture
def sync_client(sync_client_db_reset):
    """TestClient without the `with` block so the production lifespan doesn't run.

    Patches the session factory used directly inside the agent endpoint so DB
    writes hit the same in-memory SQLite engine as conftest, and depends on
    ``sync_client_db_reset`` to guarantee a clean schema — the async autouse
    fixture in conftest does not run for sync tests.
    """
    with (
        patch("app.api.v1.agent.async_session_factory", test_session_factory),
        patch("app.dependencies.async_session_factory", test_session_factory),
    ):
        yield TestClient(app)


def _register_and_get_token(sync_client: TestClient) -> str:
    response = sync_client.post("/api/v1/auth/register", json=TEST_USER)
    assert response.status_code == 201
    return response.json()["access_token"]


def test_websocket_rejects_invalid_token(sync_client):
    session_id = str(uuid.uuid4())
    with sync_client.websocket_connect(f"/api/v1/agent/ws/{session_id}?token=not-a-valid-jwt") as ws:
        event = ws.receive_json()
        assert event["type"] == "error"
        assert "auth" in event["message"].lower()


def test_websocket_rejects_empty_goal(sync_client):
    token = _register_and_get_token(sync_client)
    session_id = str(uuid.uuid4())
    with sync_client.websocket_connect(f"/api/v1/agent/ws/{session_id}?token={token}") as ws:
        ws.send_json({"goal": "   "})
        event = ws.receive_json()
        assert event["type"] == "error"
        assert "empty" in event["message"].lower()


@patch("app.api.v1.agent.agent_graph")
def test_websocket_streams_completion(mock_graph, sync_client):
    """Happy path: agent runs, final_answer persists, COMPLETE event is emitted."""
    mock_graph.invoke.return_value = {
        "goal": "Test goal",
        "final_answer": "All done.",
        "error": None,
        "is_complete": True,
    }

    token = _register_and_get_token(sync_client)
    session_id = str(uuid.uuid4())
    with sync_client.websocket_connect(f"/api/v1/agent/ws/{session_id}?token={token}") as ws:
        ws.send_json({"goal": "Test goal"})

        events = []
        while True:
            try:
                events.append(ws.receive_json())
            except Exception:
                break
            if events[-1]["type"] == "complete":
                break

    types = [e["type"] for e in events]
    assert "status" in types
    assert "complete" in types
    complete_event = next(e for e in events if e["type"] == "complete")
    assert complete_event["result"] == "All done."
    assert complete_event["status"] == "completed"


@patch("app.api.v1.agent.agent_graph")
def test_websocket_reports_agent_error(mock_graph, sync_client):
    """When the graph sets an error, final status is 'failed'."""
    mock_graph.invoke.return_value = {
        "goal": "Test goal",
        "final_answer": "",
        "error": "Model unavailable",
        "is_complete": False,
    }

    token = _register_and_get_token(sync_client)
    session_id = str(uuid.uuid4())
    with sync_client.websocket_connect(f"/api/v1/agent/ws/{session_id}?token={token}") as ws:
        ws.send_json({"goal": "Test goal"})

        events = []
        while True:
            try:
                events.append(ws.receive_json())
            except Exception:
                break
            if events[-1]["type"] == "complete":
                break

    complete_event = next(e for e in events if e["type"] == "complete")
    assert complete_event["status"] == "failed"
