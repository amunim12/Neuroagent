import logging

from langchain.tools import tool

from app.config import settings

logger = logging.getLogger(__name__)

MAX_OUTPUT_LENGTH = 5000
SANDBOX_TIMEOUT = 30


@tool
def code_executor_tool(code: str) -> str:
    """Execute Python code in a secure sandbox. Use for data analysis, calculations,
    file processing, and any task requiring code execution.
    Input: valid Python code as a string.
    Returns: stdout output, any errors, and results."""
    if not code or not code.strip():
        return "Error: code cannot be empty."

    from e2b_code_interpreter import Sandbox

    try:
        with Sandbox(api_key=settings.E2B_API_KEY, timeout=SANDBOX_TIMEOUT) as sandbox:
            execution = sandbox.run_code(code.strip())

            parts: list[str] = []
            if execution.logs.stdout:
                stdout = "\n".join(execution.logs.stdout)
                parts.append(f"Output:\n{stdout}")
            if execution.logs.stderr:
                stderr = "\n".join(execution.logs.stderr)
                parts.append(f"Errors:\n{stderr}")
            if execution.results:
                parts.append(f"Results:\n{execution.results[0]}")

            output = "\n".join(parts) or "Code executed successfully with no output."

            # Truncate overly long output to stay within context limits
            if len(output) > MAX_OUTPUT_LENGTH:
                output = output[:MAX_OUTPUT_LENGTH] + f"\n\n... (truncated, {len(output)} total chars)"

            return output
    except Exception as e:
        logger.error("E2B code execution failed: %s", e)
        return f"Execution failed: {e}"
