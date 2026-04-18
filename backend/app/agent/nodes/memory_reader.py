import logging

from app.agent.memory.long_term import LongTermMemory
from app.agent.state import AgentState

logger = logging.getLogger(__name__)


async def memory_reader_node(state: AgentState) -> dict:
    """Retrieve semantically relevant memories for the current goal."""
    try:
        memory = LongTermMemory()
        results = await memory.search(
            query=state["goal"],
            namespace=state["user_id"],
            top_k=5,
        )
        return {"retrieved_memory": results}
    except Exception as e:
        # Memory retrieval is non-critical; log and continue with empty context
        logger.warning("Memory retrieval failed: %s", e)
        return {"retrieved_memory": []}
