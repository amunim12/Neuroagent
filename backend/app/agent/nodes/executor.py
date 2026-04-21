import json
import logging
import re

from langchain_core.messages import ToolMessage
from langchain_core.prompts import ChatPromptTemplate

from app.agent.models.clients import get_llm
from app.agent.state import AgentState
from app.agent.tools.api_caller import api_caller_tool
from app.agent.tools.browser import browser_tool
from app.agent.tools.code_executor import code_executor_tool
from app.agent.tools.web_search import web_search_tool

logger = logging.getLogger(__name__)

TOOLS = [web_search_tool, code_executor_tool, browser_tool, api_caller_tool]
TOOL_MAP = {t.name: t for t in TOOLS}

EXECUTOR_SYSTEM_PROMPT = """Execute the subtask using available tools. Return a concise result."""

# Matches Llama's malformed XML-style tool call:
# <function=tool_name{"arg": "value"}></function>
_MALFORMED_TOOL_RE = re.compile(r"<function=(\w+)(\{.*?\})(?:</function>)?", re.DOTALL)


def _parse_malformed_tool_call(error_str: str) -> tuple[str, dict] | None:
    """Extract tool name + args from a Groq 'tool_use_failed' error string."""
    match = _MALFORMED_TOOL_RE.search(error_str)
    if not match:
        return None
    tool_name = match.group(1)
    try:
        args = json.loads(match.group(2))
        return tool_name, args
    except json.JSONDecodeError:
        return None


def _run_tool(tool_name: str, args: dict) -> str:
    tool_fn = TOOL_MAP.get(tool_name)
    if tool_fn is None:
        return f"Unknown tool: {tool_name}"
    try:
        return str(tool_fn.invoke(args))
    except Exception as exc:
        return f"Tool error: {exc}"


def executor_node(state: AgentState) -> dict:
    """Execute the current subtask using the selected model and available tools."""
    subtasks = state.get("subtasks", [])
    current_index = state.get("current_task_index", 0)
    current_task = subtasks[current_index] if subtasks and current_index < len(subtasks) else state["goal"]

    model_name = state.get("selected_model", "gpt-4o")
    llm = get_llm(model_name, streaming=False)
    llm_with_tools = llm.bind_tools(TOOLS)

    # Build context from previous step outputs (last 2, capped at 200 chars each)
    previous_context = ""
    recent_outputs = state.get("tool_outputs", [])[-2:]
    if recent_outputs:
        previous_context = "\n\nPrevious:\n" + "\n".join(
            f"- {r['task']}: {r['output'][:200]}" for r in recent_outputs
        )

    prompt = ChatPromptTemplate.from_messages([
        ("system", EXECUTOR_SYSTEM_PROMPT),
        ("human", "Subtask: {task}{context}"),
    ])

    messages = prompt.format_messages(task=current_task, context=previous_context)
    callback = state.get("stream_callback")
    final_output = "Task completed."

    try:
        max_iterations = 3
        for _iteration in range(max_iterations):
            try:
                response = llm_with_tools.invoke(messages)
            except Exception as invoke_err:
                error_str = str(invoke_err)
                # Groq rejects Llama's XML-style tool calls — parse and run manually.
                if "tool_use_failed" in error_str or "tool call validation failed" in error_str:
                    parsed = _parse_malformed_tool_call(error_str)
                    if parsed:
                        tool_name, tool_args = parsed
                        logger.warning("Recovering malformed tool call: %s(%s)", tool_name, tool_args)
                        tool_result = _run_tool(tool_name, tool_args)
                        if callback:
                            callback({
                                "type": "tool_call",
                                "tool": tool_name,
                                "input": str(tool_args)[:500],
                                "output": str(tool_result)[:500],
                                "model": model_name,
                                "subtask": current_task,
                            })
                        final_output = tool_result[:800]
                    else:
                        logger.error("Could not parse malformed tool call: %s", error_str)
                        final_output = f"Tool call failed: {error_str[:200]}"
                    break
                raise

            messages.append(response)

            if not response.tool_calls:
                final_output = response.content if response.content else "Task completed."
                break

            for tool_call in response.tool_calls:
                tool_result = _run_tool(tool_call["name"], tool_call["args"])

                if callback:
                    callback({
                        "type": "tool_call",
                        "tool": tool_call["name"],
                        "input": str(tool_call["args"])[:500],
                        "output": str(tool_result)[:500],
                        "model": model_name,
                        "subtask": current_task,
                    })

                messages.append(ToolMessage(content=str(tool_result)[:800], tool_call_id=tool_call["id"]))
        else:
            # Exhausted iterations — use last response content
            if hasattr(response, "content") and response.content:
                final_output = response.content

        updated_tool_outputs = state.get("tool_outputs", []) + [{"task": current_task, "output": final_output}]
        return {
            "tool_outputs": updated_tool_outputs,
            "current_task_index": current_index + 1,
        }

    except Exception as e:
        logger.error("Executor error: %s", e)
        if callback:
            callback({"type": "error", "message": str(e)})
        return {"error": str(e), "is_complete": True}
