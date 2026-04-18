from datetime import datetime

from pydantic import BaseModel


class SessionCreate(BaseModel):
    goal: str


class SessionResponse(BaseModel):
    id: str
    goal: str
    status: str
    result: str | None = None
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class SessionListResponse(BaseModel):
    sessions: list[SessionResponse]
    total: int
