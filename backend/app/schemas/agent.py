from pydantic import BaseModel, Field


class AgentRunRequest(BaseModel):
    goal: str = Field(..., min_length=1, description="Natural language goal for the agent to execute")


class AgentRunResponse(BaseModel):
    session_id: str
    status: str
