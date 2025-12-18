from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, field_validator
from typing import List
import uuid

from ..database import get_db, Agent
from ...utils.agent_prompt_generator import generate_agent_prompt
from ...utils.logger import get_logger, log_error
from ...utils.validators import (
    validate_agent_name,
    validate_agent_description,
    ValidationError as ValidatorError
)

router = APIRouter()
logger = get_logger(__name__)

# Request/Response models
class AgentCreate(BaseModel):
    name: str
    description: str  # User's description of what agent should do
    
    @field_validator('name')
    @classmethod
    def validate_name_field(cls, v):
        try:
            return validate_agent_name(v)
        except ValidatorError as e:
            raise ValueError(str(e))
    
    @field_validator('description')
    @classmethod
    def validate_description_field(cls, v):
        try:
            return validate_agent_description(v)
        except ValidatorError as e:
            raise ValueError(str(e))

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
    logger.info(f"Listed agents", extra={
        'extra_fields': {'count': len(agents)}
    })
    return agents

@router.post("/agents", response_model=AgentResponse)
async def create_agent(agent: AgentCreate, db: Session = Depends(get_db)):
    """Create a new agent with AI-generated system prompt"""
    try:
        logger.info(f"Generating prompt for agent", extra={
            'extra_fields': {
                'agent_name': agent.name,
                'description_length': len(agent.description)
            }
        })
        
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
        
        logger.info(f"Created agent successfully", extra={
            'extra_fields': {
                'agent_id': new_agent.id,
                'agent_name': agent.name,
                'prompt_length': len(generated.system_prompt)
            }
        })
        
        return new_agent
    except Exception as e:
        log_error(
            error=e,
            context="create_agent",
            agent_name=agent.name
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/agents/{agent_id}")
async def delete_agent(agent_id: str, db: Session = Depends(get_db)):
    """Delete an agent"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        logger.warning(f"Agent not found for deletion", extra={
            'extra_fields': {'agent_id': agent_id}
        })
        raise HTTPException(status_code=404, detail="Agent not found")
    
    agent_name = agent.name
    db.delete(agent)
    db.commit()
    
    logger.info(f"Deleted agent", extra={
        'extra_fields': {
            'agent_id': agent_id,
            'agent_name': agent_name
        }
    })
    
    return {"message": "Agent deleted successfully"}

