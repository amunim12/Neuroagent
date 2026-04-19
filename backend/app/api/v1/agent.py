import asyncio
import logging
import uuid

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.graph import agent_graph
from app.agent.state import AgentState
from app.db.base import async_session_factory, get_async_session
from app.db.models import AgentSession, User
from app.dependencies import authenticate_websocket, get_current_user
from app.schemas.agent import AgentRunRequest, AgentRunResponse
from app.services.session_service import create_session
from app.utils.streaming import EventType, format_event, make_stream_callback
from app.utils.tracing import run_config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent", tags=["agent"])

# Interval (seconds) for draining pending events to the WebSocket
EVENT_DRAIN_INTERVAL = 0.1


@router.websocket("/ws/{session_id}")
async def agent_websocket(websocket: WebSocket, session_id: str):
    """WebSocket endpoint that runs the agent and streams events in real time.

    Flow:
    1. Client connects with ?token=<jwt> query param
    2. Client sends JSON: {"goal": "..."}
    3. Server streams agent events as JSON messages
    4. Server sends a final "complete" event and closes
    """
    await websocket.accept()

    # Authenticate via query param
    user = await authenticate_websocket(websocket)
    if user is None:
        await websocket.send_json(format_event(EventType.ERROR, message="Authentication failed"))
        await websocket.close(code=4001, reason="Unauthorized")
        return

    try:
        # Receive goal from client
        data = await asyncio.wait_for(websocket.receive_json(), timeout=30)
        goal = data.get("goal", "").strip()
        if not goal:
            await websocket.send_json(format_event(EventType.ERROR, message="Goal cannot be empty"))
            await websocket.close(code=4000, reason="Empty goal")
            return

        # Persist session to DB
        async with async_session_factory() as db:
            session_uuid = uuid.UUID(session_id)
            db_session = AgentSession(id=session_uuid, user_id=user.id, goal=goal, status="running")
            db.add(db_session)
            await db.commit()

        await websocket.send_json(format_event(EventType.STATUS, message="Agent started", session_id=session_id))

        # Create the stream callback and pending events list
        callback, pending_events = make_stream_callback(websocket.send_json)

        # Build initial agent state
        initial_state: AgentState = {
            "goal": goal,
            "session_id": session_id,
            "user_id": str(user.id),
            "messages": [],
            "subtasks": [],
            "current_task_index": 0,
            "tool_outputs": [],
            "retrieved_memory": [],
            "selected_model": "gpt-4o",
            "final_answer": "",
            "is_complete": False,
            "error": None,
            "stream_callback": callback,
        }

        # Run the agent graph in a background thread (it's CPU-bound / sync).
        # run_config attaches user/session metadata so LangSmith traces are filterable.
        config = run_config(session_id=session_id, user_id=str(user.id), goal=goal)
        loop = asyncio.get_running_loop()
        agent_task = loop.run_in_executor(None, lambda: agent_graph.invoke(initial_state, config=config))

        # Drain pending events to WebSocket while the agent runs
        while not agent_task.done():
            await asyncio.sleep(EVENT_DRAIN_INTERVAL)
            while pending_events:
                event = pending_events.pop(0)
                try:
                    await websocket.send_json(event)
                except WebSocketDisconnect:
                    agent_task.cancel()
                    return

        # Get final state
        final_state = agent_task.result()

        # Drain any remaining events
        for event in pending_events:
            await websocket.send_json(event)
        pending_events.clear()

        # Persist result to DB
        final_answer = final_state.get("final_answer", "")
        error = final_state.get("error")
        final_status = "failed" if error else "completed"

        async with async_session_factory() as db:
            db_session = await db.get(AgentSession, session_uuid)
            if db_session:
                db_session.result = final_answer
                db_session.status = final_status
                await db.commit()

        # Send completion event
        await websocket.send_json(
            format_event(EventType.COMPLETE, session_id=session_id, result=final_answer, status=final_status)
        )

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected for session %s", session_id)
        async with async_session_factory() as db:
            db_session = await db.get(AgentSession, uuid.UUID(session_id))
            if db_session and db_session.status == "running":
                db_session.status = "cancelled"
                await db.commit()

    except TimeoutError:
        await websocket.send_json(format_event(EventType.ERROR, message="Timed out waiting for goal"))
        await websocket.close(code=4000, reason="Timeout")

    except Exception as e:
        logger.exception("Agent error for session %s: %s", session_id, e)
        try:
            await websocket.send_json(format_event(EventType.ERROR, message=str(e)))
        except Exception:
            pass

        async with async_session_factory() as db:
            db_session = await db.get(AgentSession, uuid.UUID(session_id))
            if db_session:
                db_session.status = "failed"
                await db.commit()

    finally:
        try:
            await websocket.close()
        except Exception:
            pass


@router.post("/run", response_model=AgentRunResponse, status_code=status.HTTP_202_ACCEPTED)
async def run_agent(
    body: AgentRunRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """REST fallback for triggering an agent run. Returns the session ID immediately.

    The client should then connect via WebSocket to stream events,
    or poll GET /sessions/{id} for the result.
    """
    session = await create_session(db, current_user.id, body.goal)
    return AgentRunResponse(session_id=str(session.id), status="running")
