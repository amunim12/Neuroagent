import logging

from app.agent.memory.long_term import LongTermMemory
from app.agent.state import AgentState

logger = logging.getLogger(__name__)


async def memory_writer_node(state: AgentState) -> dict:
    """Store the completed goal and result in long-term vector memory."""
    final_answer = state.get("final_answer", "")
    if not final_answer:
        return {}

    try:
        memory = LongTermMemory()
        document = f"Goal: {state['goal']}\nResult: {final_answer}"
        await memory.upsert(
            text=document,
            namespace=state["user_id"],
            metadata={"session_id": state["session_id"], "goal": state["goal"]},
        )
    except Exception as e:
        # Memory persistence is non-critical; log and continue
        logger.warning("Memory write failed: %s", e)

    return {}
