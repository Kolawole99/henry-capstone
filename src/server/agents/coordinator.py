from langfuse import observe
from src.server.models.schemas import UserQuery
from src.server.agents.dispatcher import DispatcherAgent
from src.server.agents.specialist import SpecialistAgent
from src.server.agents.auditor import AuditorAgent

class Coordinator:
    def __init__(self):
        print("Initializing Nexus-Mind Agents...")
        
        self.dispatcher = DispatcherAgent()
        self.specialist = SpecialistAgent()
        self.auditor = AuditorAgent()
        print("System Ready.")

    @observe(name="coordinator_process_query", as_type="chain")
    def process_query(self, query_text: str, user_role: str = "employee", agent_id: str = None):
        print(f"\n--- Processing Query: {query_text} ---")
        
        # 1. Parse Input
        query = UserQuery(query_text=query_text, user_role=user_role)
        
        # 2. Route Query
        print("Dispatcher analyzing...")
        
        # Check if agents exist
        from ..api.database import SessionLocal, Agent
        db = SessionLocal()
        try:
            agent_count = db.query(Agent).count()
            if agent_count == 0:
                return {
                    "final_answer": "No agents are available. Please create at least one agent in the Settings page to get started.",
                    "agent_name": "System",
                    "sources": []
                }
        finally:
            db.close()
        
        routing = self.dispatcher.route_query(query)
        print(f"Routed to: {routing.agent_name} (Confidence: {routing.confidence})")
        print(f"Reasoning: {routing.reasoning}")

        # 3. Specialist Execution (RAG)
        print(f"Specialist ({routing.agent_name}) working...")
        agent_response = self.specialist.generate_response(query, routing, agent_id=routing.agent_id)
        print(f"Draft Answer: {agent_response.answer[:100]}...")

        # 4. Audit
        print("Auditor reviewing...")
        audit_result = self.auditor.audit_response(query, agent_response)
        print(f"Audit: {'PASS' if audit_result.is_safe else 'FAIL'}")

        # 5. Return Final Result
        return {
            "final_answer": audit_result.final_answer,
            "agent_name": routing.agent_name,
            "sources": agent_response.sources
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
