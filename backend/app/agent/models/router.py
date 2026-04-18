from app.agent.models.clients import MODEL_CLAUDE_SONNET, MODEL_GPT4O, MODEL_GROQ_LLAMA3

# Keywords that suggest simple retrieval tasks (fast, cheap model)
SIMPLE_KEYWORDS = ["summarize", "find", "search", "list", "what is", "define", "look up", "who is"]

# Keywords that suggest structured/coding tasks (strong reasoning model)
CODING_KEYWORDS = ["code", "write", "debug", "analyze", "compare", "implement", "refactor", "fix", "build"]


def route_model_for_task(task: str) -> str:
    """
    Select the most cost-effective model based on task complexity.

    Routing heuristic:
    - Simple retrieval/summarization -> groq-llama3 (fast, cheap)
    - Coding and structured analysis -> claude-sonnet (reliable reasoning)
    - Complex multi-step or ambiguous  -> gpt-4o (most capable)
    """
    task_lower = task.lower()

    if any(keyword in task_lower for keyword in SIMPLE_KEYWORDS):
        return MODEL_GROQ_LLAMA3

    if any(keyword in task_lower for keyword in CODING_KEYWORDS):
        return MODEL_CLAUDE_SONNET

    return MODEL_GPT4O
