"""Tests for the agent WebSocket and REST endpoints."""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

# Unique per-test emails are belt-and-suspenders on top of the per-test DB
# isolation provided by the fixtures in conftest.py.
PASSWORD = "securepassword123"


def _make_user() -> dict[str, str]:
    return {"email": f"agent-user-{uuid.uuid4()}@example.com", "password": PASSWORD}


# === REST fallback ===


@pytest.mark.asyncio
async def test_run_agent_requires_auth(client: AsyncClient):
    response = await client.post("/api/v1/agent/run", json={"goal": "Do something"})
    # FastAPI < 0.118 returns 403 for missing HTTPBearer credentials; newer
    # versions return 401. Accept both so the suite works across the pinned range.
    assert response.status_code in {401, 403}


@pytest.mark.asyncio
async def test_run_agent_returns_session_id(client: AsyncClient):
    register = await client.post("/api/v1/auth/register", json=_make_user())
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
    register = await client.post("/api/v1/auth/register", json=_make_user())
    token = register.json()["access_token"]

    response = await client.post(
        "/api/v1/agent/run",
        json={"goal": ""},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 422


# === WebSocket ===
# The sync_client fixture lives in conftest.py so it can share the per-test
# engine machinery used by the async tests.


def _register_and_get_token(sync_client: TestClient) -> str:
    response = sync_client.post("/api/v1/auth/register", json=_make_user())
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
    mock_graph.ainvoke = AsyncMock(return_value={
        "goal": "Test goal",
        "final_answer": "All done.",
        "error": None,
        "is_complete": True,
    })

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
    mock_graph.ainvoke = AsyncMock(return_value={
        "goal": "Test goal",
        "final_answer": "",
        "error": "Model unavailable",
        "is_complete": False,
    })

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
