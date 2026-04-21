from app.config import settings


def route_model_for_task(task: str) -> str:  # noqa: ARG001
    """Return the model to use for a given task.

    Routing defers entirely to DEFAULT_AGENT_MODEL so the operator can steer
    away from a provider whose quota is exhausted without changing code.
    """
    return settings.DEFAULT_AGENT_MODEL
