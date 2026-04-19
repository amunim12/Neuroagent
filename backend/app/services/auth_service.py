from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User
from app.utils.security import hash_password, verify_password


async def create_user(db: AsyncSession, email: str, password: str) -> User:
    """Register a new user. Raises ValueError if email already taken.

    Atomic: relies on the UNIQUE constraint on ``users.email`` instead of a
    separate SELECT, which would otherwise leave a TOCTOU race between the
    existence check and the insert under concurrent registrations.
    """
    user = User(email=email, hashed_password=hash_password(password))
    db.add(user)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise ValueError("Email already registered") from None
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    """Verify credentials and return the User, or None if invalid."""
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


async def get_user_by_id(db: AsyncSession, user_id: str) -> User | None:
    """Fetch a user by primary key."""
    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    return result.scalar_one_or_none()
