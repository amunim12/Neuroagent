from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from app.agent.models.clients import get_llm
from app.agent.state import AgentState
from app.config import settings

PLANNER_SYSTEM_PROMPT = """You are a task planner. Decompose the goal into 2-4 concrete subtasks \
using tools: web_search, code_executor, browser, api_caller. Be specific and brief."""


class TaskPlan(BaseModel):
    """Structured output for the planner node."""

    subtasks: list[str] = Field(description="Ordered list of 2-4 concrete subtasks")


def planner_node(state: AgentState) -> dict:
    """Decompose the user's goal into ordered subtasks using the default model."""
    llm = get_llm(settings.DEFAULT_AGENT_MODEL, streaming=False).with_structured_output(TaskPlan)

    memory_context = "\n".join(state.get("retrieved_memory", []))[:300] or "None."

    prompt = ChatPromptTemplate.from_messages([
        ("system", PLANNER_SYSTEM_PROMPT),
        ("human", "Goal: {goal}\n\nMemory: {memory}"),
    ])

    chain = prompt | llm
    result: TaskPlan = chain.invoke({"goal": state["goal"], "memory": memory_context})

    callback = state.get("stream_callback")
    if callback:
        callback({
            "type": "planning",
            "subtasks": result.subtasks,
            "reasoning": "",
        })

    return {"subtasks": result.subtasks, "current_task_index": 0}
