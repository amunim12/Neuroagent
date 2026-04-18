from langgraph.graph import END, StateGraph

from app.agent.nodes.executor import executor_node
from app.agent.nodes.memory_reader import memory_reader_node
from app.agent.nodes.memory_writer import memory_writer_node
from app.agent.nodes.planner import planner_node
from app.agent.nodes.router import model_router_node
from app.agent.nodes.synthesizer import synthesizer_node
from app.agent.state import AgentState


def should_continue(state: AgentState) -> str:
    """Conditional edge: continue executing subtasks or move to synthesis."""
    if state.get("error"):
        return "synthesize"

    if state.get("is_complete"):
        return END

    current_index = state.get("current_task_index", 0)
    subtasks = state.get("subtasks", [])

    if current_index >= len(subtasks):
        return "synthesize"

    return "route_model"


def build_agent_graph() -> StateGraph:
    """Construct and compile the NeuroAgent LangGraph workflow.

    Flow:
        read_memory -> plan -> route_model -> execute -> (loop or synthesize) -> write_memory -> END
    """
    workflow = StateGraph(AgentState)

    # Register nodes
    workflow.add_node("read_memory", memory_reader_node)
    workflow.add_node("plan", planner_node)
    workflow.add_node("route_model", model_router_node)
    workflow.add_node("execute", executor_node)
    workflow.add_node("synthesize", synthesizer_node)
    workflow.add_node("write_memory", memory_writer_node)

    # Entry point
    workflow.set_entry_point("read_memory")

    # Linear edges
    workflow.add_edge("read_memory", "plan")
    workflow.add_edge("plan", "route_model")
    workflow.add_edge("route_model", "execute")

    # Conditional loop: after execution, either loop back for next subtask or synthesize
    workflow.add_conditional_edges(
        "execute",
        should_continue,
        {
            "route_model": "route_model",
            "synthesize": "synthesize",
            END: END,
        },
    )

    # After synthesis, persist to memory then finish
    workflow.add_edge("synthesize", "write_memory")
    workflow.add_edge("write_memory", END)

    return workflow.compile()


# Pre-compiled graph instance for use across the application
agent_graph = build_agent_graph()
