from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
import uuid

from ..database import get_db, Agent
from ...utils.agent_prompt_generator import generate_agent_prompt

router = APIRouter()

# Request/Response models
class AgentCreate(BaseModel):
    name: str
    description: str  # User's description of what agent should do

class AgentResponse(BaseModel):
    id: str
    name: str
    description: str  # Refined description
    system_prompt: str

    class Config:
        from_attributes = True

@router.get("/agents", response_model=List[AgentResponse])
async def list_agents(db: Session = Depends(get_db)):
    """Get all agents"""
    agents = db.query(Agent).all()
    return agents

@router.post("/agents", response_model=AgentResponse)
async def create_agent(agent: AgentCreate, db: Session = Depends(get_db)):
    """Create a new agent with AI-generated system prompt"""
    try:
        print(f"Generating prompt for agent: {agent.name}")
        generated = generate_agent_prompt(agent.name, agent.description)
        
        new_agent = Agent(
            id=str(uuid.uuid4()),
            name=agent.name,
            description=generated.refined_description,
            system_prompt=generated.system_prompt
        )
        db.add(new_agent)
        db.commit()
        db.refresh(new_agent)
        
        print(f"✓ Created agent '{agent.name}' with generated prompt")
        return new_agent
    except Exception as e:
        print(f"Error creating agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/agents/{agent_id}")
async def delete_agent(agent_id: str, db: Session = Depends(get_db)):
    """Delete an agent"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    db.delete(agent)
    db.commit()
    return {"message": "Agent deleted successfully"}
