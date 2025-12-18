import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from src.server.models.schemas import UserQuery, RoutingDecision
from src.server.utils.prompt_loader import load_prompt

class DispatcherAgent:
    def __init__(self):
        base_url = os.getenv("OPENAI_BASE_URL")
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, base_url=base_url)
        self.system_prompt = load_prompt('dispatcher')

    def route_query(self, query: UserQuery) -> RoutingDecision:
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("user", "User Role: {user_role}\nQuery: {query_text}")
        ])
        
        chain = prompt | self.llm.with_structured_output(RoutingDecision)
        
        result = chain.invoke({
            "query_text": query.query_text,
            "user_role": query.user_role or "employee"
        })
        return result
