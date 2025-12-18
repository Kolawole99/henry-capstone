import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langfuse import observe

from src.server.models.schemas import UserQuery, RoutingDecision
from src.server.utils.prompt_loader import load_prompt

class DispatcherAgent:
    def __init__(self):
        base_url = os.getenv("OPENAI_BASE_URL")
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, base_url=base_url)
        self.system_prompt = load_prompt('dispatcher')

    @observe(name="dispatcher_route_query", as_type="generation")
    def route_query(self, query: UserQuery) -> RoutingDecision:
        # Import here to avoid circular dependency
        from ..api.database import SessionLocal, Agent
        
        # Fetch available agents from database
        db = SessionLocal()
        try:
            agents = db.query(Agent).all()
            agent_list = "\n".join([
                f"- ID: {agent.id}, Name: {agent.name}, Description: {agent.description}"
                for agent in agents
            ])
        finally:
            db.close()
        
        # Create prompt with available agents
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("user", "Available Agents:\n{agent_list}\n\nUser Query: {query}\n\nRoute this query to the best agent.")
        ])
        
        # Create chain with structured output
        chain = prompt | self.llm.with_structured_output(RoutingDecision)
        
        # Invoke chain
        result = chain.invoke({
            "agent_list": agent_list if agent_list else "No agents available",
            "query": query.query_text
        })
        
        return result
