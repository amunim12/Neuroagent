from langchain.tools import tool

from app.config import settings


@tool
def code_executor_tool(code: str) -> str:
    """Execute Python code in a secure sandbox. Use for data analysis, calculations,
    file processing, and any task requiring code execution.
    Input: valid Python code as a string.
    Returns: stdout output, any errors, and results."""
    from e2b_code_interpreter import Sandbox

    try:
        with Sandbox(api_key=settings.E2B_API_KEY) as sandbox:
            execution = sandbox.run_code(code)

            parts: list[str] = []
            if execution.logs.stdout:
                parts.append("Output:\n" + "\n".join(execution.logs.stdout))
            if execution.logs.stderr:
                parts.append("Errors:\n" + "\n".join(execution.logs.stderr))
            if execution.results:
                parts.append("Results:\n" + str(execution.results[0]))

            return "\n".join(parts) or "Code executed successfully with no output."
    except Exception as e:
        return f"Execution failed: {e}"
