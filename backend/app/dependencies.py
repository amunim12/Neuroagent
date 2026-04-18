from fastapi import Depends, HTTPException, WebSocket, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import async_session_factory, get_async_session
from app.db.models import User
from app.services.auth_service import get_user_by_id
from app.utils.security import verify_token

security_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: AsyncSession = Depends(get_async_session),
) -> User:
    """Extract and validate the JWT, then return the authenticated User."""
    user_id = verify_token(credentials.credentials)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    user = await get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user


async def authenticate_websocket(websocket: WebSocket) -> User | None:
    """Authenticate a WebSocket connection using a JWT passed as a ?token= query parameter.

    Called manually (not via Depends) from the WebSocket handler, so we read
    the query param off the WebSocket object directly.

    Returns the User if valid, or None if authentication fails (caller should close the socket).
    """
    token = websocket.query_params.get("token")
    if not token:
        return None

    user_id = verify_token(token)
    if user_id is None:
        return None

    async with async_session_factory() as db:
        user = await get_user_by_id(db, user_id)
        return user
