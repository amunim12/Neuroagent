from typing import Annotated, Any

from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class AgentState(TypedDict):
    """State that flows through every node in the agent graph."""

    # Core identifiers
    goal: str
    session_id: str
    user_id: str

    # Message history (LangGraph-managed accumulation)
    messages: Annotated[list, add_messages]

    # Planning
    subtasks: list[str]
    current_task_index: int

    # Execution
    tool_outputs: list[dict[str, Any]]
    retrieved_memory: list[str]

    # Multi-model routing
    selected_model: str  # "gpt-4o" | "claude-sonnet" | "groq-llama3"

    # Output
    final_answer: str
    is_complete: bool
    error: str | None

    # WebSocket streaming callback (set at runtime, not serialized)
    stream_callback: Any
