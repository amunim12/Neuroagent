"""Utilities for formatting and sending agent events over WebSocket."""

import logging
from datetime import UTC, datetime
from enum import StrEnum

logger = logging.getLogger(__name__)


class EventType(StrEnum):
    """All event types the agent can emit to the frontend."""

    PLANNING = "planning"
    ROUTING = "routing"
    TOOL_CALL = "tool_call"
    THINKING = "thinking"
    FINAL_ANSWER = "final_answer"
    COMPLETE = "complete"
    ERROR = "error"
    STATUS = "status"


def format_event(event_type: EventType | str, **payload) -> dict:
    """Build a timestamped event dict for WebSocket transmission."""
    return {
        "type": str(event_type),
        "timestamp": datetime.now(UTC).isoformat(),
        **payload,
    }


def make_stream_callback(send_fn):
    """Create a synchronous callback that queues events for async WebSocket sending.

    The LangGraph nodes call this callback synchronously. We store the events
    in a list that the WebSocket handler drains and sends asynchronously.

    Args:
        send_fn: An async callable that sends a dict as JSON over the WebSocket.

    Returns:
        A tuple of (callback, pending_events_list).
        - callback: synchronous function the nodes call with event dicts.
        - pending_events_list: list that accumulates events for async sending.
    """
    pending: list[dict] = []

    def callback(event: dict) -> None:
        timestamped = {
            "timestamp": datetime.now(UTC).isoformat(),
            **event,
        }
        pending.append(timestamped)

    return callback, pending
