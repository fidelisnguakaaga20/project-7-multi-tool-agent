from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

from app.agent.runner import run_agent

router = APIRouter(prefix="/agent", tags=["agent"])


class AgentChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None


class AgentChatResponse(BaseModel):
    answer: str
    trace: List[Dict[str, Any]]
    citations: List[str] = []
    thoughtless_plan: List[str] = []


@router.post("/chat", response_model=AgentChatResponse)
def agent_chat(payload: AgentChatRequest):
    result = run_agent(message=payload.message, conversation_id=payload.conversation_id)
    return result
