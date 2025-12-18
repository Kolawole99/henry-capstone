import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from langfuse import observe
from src.server.models.schemas import UserQuery, RoutingDecision, AgentResponse
from src.server.utils.vector_store import VectorStoreManager
from src.server.utils.prompt_loader import load_prompt

class SpecialistAgent:
    def __init__(self):
        base_url = os.getenv("OPENAI_BASE_URL")
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0, base_url=base_url)
        
    @observe(name="specialist_generate_response", as_type="generation")
    def generate_response(self, query: UserQuery, routing: RoutingDecision, agent_id: str = None) -> AgentResponse:
        if agent_id:
            from ..api.database import SessionLocal, Agent
            
            db = SessionLocal()
            try:
                agent = db.query(Agent).filter(Agent.id == agent_id).first()
                if agent and agent.system_prompt:
                    system_prompt = f"{agent.system_prompt}\n\n{{context}}"
                else:
                    system_prompt = "You are a helpful assistant.\n\n{context}"
            finally:
                db.close()
            
            vector_store_manager = VectorStoreManager(agent_id=agent_id)
            retriever = vector_store_manager.get_retriever()
        else:
            system_prompt = "You are a helpful assistant.\n\n{context}"
            vector_store_manager = VectorStoreManager()
            retriever = vector_store_manager.get_retriever()

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}"),
        ])

        question_answer_chain = create_stuff_documents_chain(self.llm, prompt)
        rag_chain = create_retrieval_chain(retriever, question_answer_chain)

        response = rag_chain.invoke({"input": query.query_text})
        
        sources = [doc.metadata.get("source", "unknown") for doc in response.get("context", [])]
        unique_sources = list(set(sources))

        return AgentResponse(
            answer=response["answer"],
            sources=unique_sources,
            agent_name=f"{routing.department}_Specialist"
        )
