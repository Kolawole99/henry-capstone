import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel
from langfuse import observe
from .prompt_loader import load_prompt

class GeneratedAgentPrompt(BaseModel):
    """Generated prompt and refined description for an agent"""
    system_prompt: str
    refined_description: str

@observe(name="agent_prompt_generator", as_type="generation")
def generate_agent_prompt(agent_name: str, user_description: str) -> GeneratedAgentPrompt:
    """
    Generate a specialized system prompt and refined description for an agent.
    
    Args:
        agent_name: The name of the agent (e.g., "Finance Specialist")
        user_description: User's description of what the agent should do
        
    Returns:
        GeneratedAgentPrompt with system_prompt and refined_description
    """
    base_url = os.getenv("OPENAI_BASE_URL")
    llm = ChatOpenAI(model="gpt-4o", temperature=0.7, base_url=base_url)
    
    generator_template = load_prompt('agent_generator')
    prompt = ChatPromptTemplate.from_messages([
        ("system", generator_template),
        ("user", "Now generate for:\nAgent Name: {agent_name}\nUser Description: {user_description}")
    ])
    
    chain = prompt | llm.with_structured_output(GeneratedAgentPrompt)
    result = chain.invoke({
        "agent_name": agent_name,
        "user_description": user_description
    })
    
    return result
