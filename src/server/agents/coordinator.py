# from langfuse.decorators import observe
from src.server.models.schemas import UserQuery
from src.server.agents.dispatcher import DispatcherAgent
from src.server.agents.specialist import SpecialistAgent
from src.server.agents.auditor import AuditorAgent
from src.server.utils.vector_store import VectorStoreManager

class Coordinator:
    def __init__(self):
        print("Initializing Nexus-Mind Agents...")
        self.vector_store_manager = VectorStoreManager()
        # Ensure data is ready (simple check)
        self.vector_store_manager.ingest_data()
        
        self.dispatcher = DispatcherAgent()
        self.specialist = SpecialistAgent(self.vector_store_manager)
        self.auditor = AuditorAgent()
        print("System Ready.")

    # @observe(as_type="generation")
    def process_query(self, query_text: str, user_role: str = "employee"):
        print(f"\n--- Processing Query: {query_text} ---")
        
        # 1. Parse Input
        query = UserQuery(query_text=query_text, user_role=user_role)
        
        # 2. Dispatch
        print("Dispatcher analyzing...")
        routing = self.dispatcher.route_query(query)
        print(f"Routed to: {routing.department} (Confidence: {routing.confidence})")
        print(f"Reasoning: {routing.reasoning}")

        if routing.department == "GENERAL":
            return {
                "final_answer": "I can only help with HR or Technical questions at this time.",
                "sources": [],
                "department": "GENERAL"
            }

        # 3. Specialist Execution (RAG)
        print(f"Specialist ({routing.department}) working...")
        agent_response = self.specialist.generate_response(query, routing)
        print(f"Draft Answer: {agent_response.answer[:100]}...")

        # 4. Audit
        print("Auditor reviewing...")
        audit = self.auditor.audit_response(query.query_text, agent_response)
        
        if audit.is_safe:
            print("Audit PASSED.")
            final_output = audit.final_answer or agent_response.answer
        else:
            print("Audit FAILED. Rewriting...")
            print(f"Feedback: {audit.feedback}")
            final_output = audit.final_answer

        return {
            "final_answer": final_output,
            "sources": agent_response.sources,
            "department": routing.department,
            "audit_feedback": audit.feedback if not audit.is_safe else None
        }

if __name__ == "__main__":
    # Simple CLI test
    system = Coordinator()
    
    while True:
        try:
            user_input = input("\nEnter your question (or 'exit'): ")
            if user_input.lower() in ["exit", "quit"]:
                break
            
            result = system.process_query(user_input)
            print("\n>>> FINAL RESPONSE:")
            print(result["final_answer"])
            if result["sources"]:
                print(f"\nSources: {result['sources']}")
        except KeyboardInterrupt:
            break
