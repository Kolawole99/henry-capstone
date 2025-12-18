import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langfuse import observe
from src.server.models.schemas import UserQuery, AgentResponse, AuditResult
from src.server.utils.prompt_loader import load_prompt

class AuditorAgent:
    def __init__(self):
        base_url = os.getenv("OPENAI_BASE_URL")
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0, base_url=base_url)
        self.system_prompt = load_prompt('auditor')

    @observe(name="auditor_audit_response", as_type="generation")
    def audit_response(self, query: UserQuery, agent_response: AgentResponse) -> AuditResult:
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("user", "User Query: {query}\n\nAgent Response: {response}\n\nAudit this response.")
        ])
        
        chain = prompt | self.llm.with_structured_output(AuditResult)
        
        result = chain.invoke({
            "query": query.query_text,
            "response": agent_response.answer
        })
        return result
