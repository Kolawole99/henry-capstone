from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
import uuid

from ..database import get_db, ChatSession, ChatMessage
from ...agents.coordinator import Coordinator

router = APIRouter()

# Initialize coordinator (singleton)
coordinator = None

def get_coordinator():
    global coordinator
    if coordinator is None:
        coordinator = Coordinator()
    return coordinator

# Request/Response models
class ChatRequest(BaseModel):
    message: str
    agent_id: Optional[str] = None
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    department: str
    sources: List[str]

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """Send a message and get AI response"""
    try:
        # Get or create session
        session_id = request.session_id or str(uuid.uuid4())
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            session = ChatSession(id=session_id)
            db.add(session)
            db.commit()
        
        # Store user message
        user_message = ChatMessage(
            session_id=session_id,
            role="user",
            content=request.message,
            agent_id=request.agent_id
        )
        db.add(user_message)
        db.commit()
        
        # Get AI response from coordinator
        coord = get_coordinator()
        result = coord.process_query(request.message, agent_id=request.agent_id)
        
        # Store assistant message
        assistant_message = ChatMessage(
            session_id=session_id,
            role="assistant",
            content=result["final_answer"],
            agent_id=request.agent_id
        )
        db.add(assistant_message)
        db.commit()
        
        return ChatResponse(
            response=result["final_answer"],
            session_id=session_id,
            department=result["department"],
            sources=result.get("sources", [])
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
