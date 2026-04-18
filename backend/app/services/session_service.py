from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AgentSession


async def create_session(db: AsyncSession, user_id: UUID, goal: str) -> AgentSession:
    """Create a new agent session for the given user."""
    session = AgentSession(user_id=user_id, goal=goal)
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def get_session(db: AsyncSession, session_id: UUID, user_id: UUID) -> AgentSession | None:
    """Fetch a single session owned by the user."""
    result = await db.execute(
        select(AgentSession).where(AgentSession.id == session_id, AgentSession.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def list_sessions(
    db: AsyncSession, user_id: UUID, limit: int = 20, offset: int = 0
) -> tuple[list[AgentSession], int]:
    """List sessions for a user with pagination. Returns (sessions, total_count)."""
    count_result = await db.execute(
        select(func.count()).select_from(AgentSession).where(AgentSession.user_id == user_id)
    )
    total = count_result.scalar_one()

    result = await db.execute(
        select(AgentSession)
        .where(AgentSession.user_id == user_id)
        .order_by(AgentSession.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    sessions = list(result.scalars().all())
    return sessions, total


async def delete_session(db: AsyncSession, session_id: UUID, user_id: UUID) -> bool:
    """Delete a session. Returns True if deleted, False if not found."""
    session = await get_session(db, session_id, user_id)
    if session is None:
        return False
    await db.delete(session)
    await db.commit()
    return True
