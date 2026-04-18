import json

import redis.asyncio as redis

from app.config import settings

SESSION_TTL_SECONDS = 3600  # 1 hour


class ShortTermMemory:
    """Ephemeral session memory backed by Redis."""

    def __init__(self):
        self.client = redis.from_url(settings.REDIS_URL)

    async def set(self, session_id: str, data: dict, ttl_seconds: int = SESSION_TTL_SECONDS) -> None:
        """Store session data with a TTL."""
        await self.client.setex(f"session:{session_id}", ttl_seconds, json.dumps(data))

    async def get(self, session_id: str) -> dict | None:
        """Retrieve session data, or None if expired/missing."""
        raw = await self.client.get(f"session:{session_id}")
        return json.loads(raw) if raw else None

    async def delete(self, session_id: str) -> None:
        """Remove session data."""
        await self.client.delete(f"session:{session_id}")
