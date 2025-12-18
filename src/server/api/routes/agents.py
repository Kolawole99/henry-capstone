from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
import uuid

from ..database import get_db, Agent

router = APIRouter()

# Request/Response models
class AgentCreate(BaseModel):
    name: str
    description: str
    department: str  # HR, TECH, GENERAL

class AgentResponse(BaseModel):
    id: str
    name: str
    description: str
    department: str

    class Config:
        from_attributes = True

@router.get("/agents", response_model=List[AgentResponse])
async def list_agents(db: Session = Depends(get_db)):
    """Get all agents"""
    agents = db.query(Agent).all()
    return agents

@router.post("/agents", response_model=AgentResponse)
async def create_agent(agent: AgentCreate, db: Session = Depends(get_db)):
    """Create a new agent"""
    new_agent = Agent(
        id=str(uuid.uuid4()),
        name=agent.name,
        description=agent.description,
        department=agent.department
    )
    db.add(new_agent)
    db.commit()
    db.refresh(new_agent)
    return new_agent

@router.delete("/agents/{agent_id}")
async def delete_agent(agent_id: str, db: Session = Depends(get_db)):
    """Delete an agent"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    db.delete(agent)
    db.commit()
    return {"message": "Agent deleted successfully"}
