import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from src.server.models.schemas import AgentResponse, AuditResult
from src.server.utils.prompt_loader import load_prompt

class AuditorAgent:
    def __init__(self):
        base_url = os.getenv("OPENAI_BASE_URL")
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0, base_url=base_url)
        self.system_prompt = load_prompt('auditor')

    def audit_response(self, original_query: str, agent_response: AgentResponse) -> AuditResult:
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("user", "User Query: {query}\nAgent Answer: {answer}\nSources: {sources}")
        ])
        
        chain = prompt | self.llm.with_structured_output(AuditResult)
        
        result = chain.invoke({
            "query": original_query,
            "answer": agent_response.answer,
            "sources": str(agent_response.sources)
        })
        return result
