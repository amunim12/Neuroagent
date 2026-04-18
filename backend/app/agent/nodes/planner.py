from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from app.agent.models.clients import get_llm
from app.agent.state import AgentState

PLANNER_SYSTEM_PROMPT = """You are an expert task planner. Decompose the user's goal into \
3-7 concrete, actionable subtasks. Each subtask should be a specific action the agent can \
take using tools like web search, code execution, or browser automation.

Order them logically. Be specific:
- Bad: "do research"
- Good: "search for current Python async best practices on the web"

Return subtasks as a list and a brief reasoning for your plan."""


class TaskPlan(BaseModel):
    """Structured output for the planner node."""

    subtasks: list[str] = Field(description="Ordered list of concrete subtasks")
    reasoning: str = Field(description="Brief explanation of the plan")


def planner_node(state: AgentState) -> dict:
    """Decompose the user's goal into ordered subtasks using GPT-4o."""
    llm = get_llm("gpt-4o", streaming=False).with_structured_output(TaskPlan)

    memory_context = "\n".join(state.get("retrieved_memory", [])) or "No prior context available."

    prompt = ChatPromptTemplate.from_messages([
        ("system", PLANNER_SYSTEM_PROMPT),
        ("human", "Goal: {goal}\n\nContext from memory:\n{memory}"),
    ])

    chain = prompt | llm
    result: TaskPlan = chain.invoke({"goal": state["goal"], "memory": memory_context})

    callback = state.get("stream_callback")
    if callback:
        callback({
            "type": "planning",
            "subtasks": result.subtasks,
            "reasoning": result.reasoning,
        })

    return {"subtasks": result.subtasks, "current_task_index": 0}
