from langchain_core.prompts import ChatPromptTemplate

from app.agent.models.clients import get_llm
from app.agent.state import AgentState
from app.agent.tools.api_caller import api_caller_tool
from app.agent.tools.browser import browser_tool
from app.agent.tools.code_executor import code_executor_tool
from app.agent.tools.web_search import web_search_tool

TOOLS = [web_search_tool, code_executor_tool, browser_tool, api_caller_tool]

EXECUTOR_SYSTEM_PROMPT = """You are an AI agent executing a specific subtask as part of a larger goal.
Use the available tools to complete the subtask. Be thorough and specific in your tool usage.
If a tool call fails, try an alternative approach before giving up.
Always return a clear, concise result summarizing what you accomplished."""


def executor_node(state: AgentState) -> dict:
    """Execute the current subtask using the selected model and available tools."""
    subtasks = state.get("subtasks", [])
    current_index = state.get("current_task_index", 0)
    current_task = subtasks[current_index] if subtasks and current_index < len(subtasks) else state["goal"]

    model_name = state.get("selected_model", "gpt-4o")
    llm = get_llm(model_name, streaming=False)
    llm_with_tools = llm.bind_tools(TOOLS)

    # Build context from previous step outputs
    previous_context = ""
    recent_outputs = state.get("tool_outputs", [])[-3:]
    if recent_outputs:
        previous_context = "\n\nContext from previous steps:\n" + "\n".join(
            f"- {r['task']}: {r['output'][:500]}" for r in recent_outputs
        )

    prompt = ChatPromptTemplate.from_messages([
        ("system", EXECUTOR_SYSTEM_PROMPT),
        ("human", "Subtask: {task}{context}"),
    ])

    messages = prompt.format_messages(task=current_task, context=previous_context)

    callback = state.get("stream_callback")

    try:
        # Iterative tool-calling loop (ReAct pattern)
        max_iterations = 5
        for _iteration in range(max_iterations):
            response = llm_with_tools.invoke(messages)
            messages.append(response)

            # Check if the model wants to call tools
            if not response.tool_calls:
                break

            # Execute each tool call
            for tool_call in response.tool_calls:
                tool_map = {t.name: t for t in TOOLS}
                tool_fn = tool_map.get(tool_call["name"])

                if tool_fn is None:
                    tool_result = f"Unknown tool: {tool_call['name']}"
                else:
                    try:
                        tool_result = tool_fn.invoke(tool_call["args"])
                    except Exception as e:
                        tool_result = f"Tool error: {e}"

                if callback:
                    callback({
                        "type": "tool_call",
                        "tool": tool_call["name"],
                        "input": str(tool_call["args"])[:500],
                        "output": str(tool_result)[:500],
                        "model": model_name,
                        "subtask": current_task,
                    })

                # Append tool result as a message for the next iteration
                from langchain_core.messages import ToolMessage

                messages.append(ToolMessage(content=str(tool_result), tool_call_id=tool_call["id"]))

        # Extract final text response
        final_output = response.content if hasattr(response, "content") and response.content else "Task completed."

        updated_tool_outputs = state.get("tool_outputs", []) + [{"task": current_task, "output": final_output}]

        return {
            "tool_outputs": updated_tool_outputs,
            "current_task_index": current_index + 1,
        }

    except Exception as e:
        if callback:
            callback({"type": "error", "message": str(e)})
        return {"error": str(e), "is_complete": True}
