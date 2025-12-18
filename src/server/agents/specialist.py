import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from src.server.models.schemas import UserQuery, RoutingDecision, AgentResponse
from src.server.utils.vector_store import VectorStoreManager
from src.server.utils.prompt_loader import load_prompt

class SpecialistAgent:
    def __init__(self, vector_store_manager: VectorStoreManager):
        base_url = os.getenv("OPENAI_BASE_URL")
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0, base_url=base_url)
        self.retriever = vector_store_manager.get_retriever()
        
    def generate_response(self, query: UserQuery, routing: RoutingDecision) -> AgentResponse:
        # Load department-specific prompt
        prompt_file_map = {
            "HR": "specialist_hr",
            "TECH": "specialist_tech",
            "GENERAL": "specialist_general"
        }
        
        prompt_name = prompt_file_map.get(routing.department, "specialist_general")
        dept_context = load_prompt(prompt_name)

        system_prompt = f"{dept_context}\n\n{{context}}"

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}"),
        ])

        question_answer_chain = create_stuff_documents_chain(self.llm, prompt)
        rag_chain = create_retrieval_chain(self.retriever, question_answer_chain)

        response = rag_chain.invoke({"input": query.query_text})
        
        # Extract sources
        sources = [doc.metadata.get("source", "unknown") for doc in response.get("context", [])]
        unique_sources = list(set(sources))

        return AgentResponse(
            answer=response["answer"],
            sources=unique_sources,
            agent_name=f"{routing.department}_Specialist"
        )
