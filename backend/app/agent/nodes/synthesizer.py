from langchain_core.prompts import ChatPromptTemplate

from app.agent.models.clients import get_llm
from app.agent.state import AgentState

SYNTHESIZER_SYSTEM_PROMPT = """You are a helpful AI assistant. Synthesize the results of all completed \
subtasks into a single, comprehensive, well-structured final answer for the user's goal.
Be specific, accurate, and actionable. Format with markdown when appropriate."""


def synthesizer_node(state: AgentState) -> dict:
    """Combine all tool outputs into a final coherent answer."""
    llm = get_llm("gpt-4o", streaming=False)

    tool_outputs = state.get("tool_outputs", [])
    results_text = "\n\n".join(
        f"Step {i + 1} ({r['task']}):\n{r['output']}" for i, r in enumerate(tool_outputs)
    )

    error = state.get("error")
    if error:
        results_text += f"\n\nNote: An error occurred during execution: {error}"

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYNTHESIZER_SYSTEM_PROMPT),
        ("human", "Original goal: {goal}\n\nCompleted subtask results:\n{results}"),
    ])

    chain = prompt | llm
    response = chain.invoke({"goal": state["goal"], "results": results_text})

    callback = state.get("stream_callback")
    if callback:
        callback({"type": "final_answer", "content": response.content})

    return {"final_answer": response.content, "is_complete": True}
