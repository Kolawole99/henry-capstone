from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
import uuid

from ..database import get_db, ChatSession, ChatMessage
from ...agents.coordinator import Coordinator
from ...utils.logger import get_logger, log_error

router = APIRouter()
logger = get_logger(__name__)

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
    """
    Process a chat message and return a response.
    Uses the coordinator to route to appropriate agent and generate response.
    """
    try:
        session = db.query(ChatSession).filter(ChatSession.id == request.session_id).first()
        if not session:
            session = ChatSession(id=request.session_id)
            db.add(session)
            db.commit()
            db.refresh(session)
            logger.info("Created new chat session", extra={
                'extra_fields': {
                    'session_id': session.id
                }
            })
        
        user_message = ChatMessage(
            session_id=session.id,
            role="user",
            content=request.message
        )
        db.add(user_message)
        db.commit()
        logger.info("Saved user message", extra={
            'extra_fields': {
                'session_id': session.id,
                'message_length': len(request.message)
            }
        })
        
        # Process query through coordinator
        logger.info("Processing query through coordinator", extra={
            'extra_fields': {
                'session_id': session.id,
                'agent_id': request.agent_id
            }
        })
        
        coord = get_coordinator() # Ensure coordinator is initialized
        result = coord.process_query(
            query_text=request.message,
            user_role="employee",
            agent_id=request.agent_id
        )
        
        logger.info("Received response from agent", extra={
            'extra_fields': {
                'session_id': session.id,
                'agent_name': result.get('agent_name', 'Unknown'),
                'sources_count': len(result.get('sources', []))
            }
        })
        
        assistant_message = ChatMessage(
            session_id=session.id,
            role="assistant",
            content=result["final_answer"],
            agent_id=request.agent_id
        )
        db.add(assistant_message)
        db.commit()
        logger.info("Saved assistant message", extra={
            'extra_fields': {
                'session_id': session.id,
                'response_length': len(result["final_answer"])
            }
        })
        
        return ChatResponse(
            response=result["final_answer"],
            session_id=session.id,
            department=result.get("agent_name", "General"),
            sources=result.get("sources", [])
        )
    except Exception as e:
        log_error(
            error=e,
            context="chat_endpoint",
            session_id=request.session_id,
            message=request.message[:100]
        )
        
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "type": type(e).__name__,
                "message": "An error occurred while processing your request. Please check the server logs for details."
            }
        )

