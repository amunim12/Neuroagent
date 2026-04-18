from app.agent.models.router import route_model_for_task
from app.agent.state import AgentState


def model_router_node(state: AgentState) -> dict:
    """Route to the most cost-effective model based on the current subtask."""
    subtasks = state.get("subtasks", [])
    current_index = state.get("current_task_index", 0)

    task = subtasks[current_index] if subtasks and current_index < len(subtasks) else state["goal"]
    selected = route_model_for_task(task)

    callback = state.get("stream_callback")
    if callback:
        callback({"type": "routing", "model": selected, "subtask": task})

    return {"selected_model": selected}
