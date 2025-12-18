from langfuse import observe
import time
from src.server.models.schemas import UserQuery
from src.server.agents.dispatcher import DispatcherAgent
from src.server.agents.specialist import SpecialistAgent
from src.server.agents.auditor import AuditorAgent
from src.server.utils.logger import get_logger, log_agent_execution

logger = get_logger(__name__)

class Coordinator:
    def __init__(self):
        logger.info("Initializing Nexus-Mind Agents...")
        
        self.dispatcher = DispatcherAgent()
        self.specialist = SpecialistAgent()
        self.auditor = AuditorAgent()
        logger.info("Nexus-Mind system ready", extra={
            'extra_fields': {
                'agents': ['dispatcher', 'specialist', 'auditor']
            }
        })

    @observe(name="coordinator_process_query", as_type="chain")
    def process_query(self, query_text: str, user_role: str = "employee", agent_id: str = None):
        start_time = time.time()
        logger.info(f"Processing query", extra={
            'extra_fields': {
                'query': query_text[:100],  # Truncate for logging
                'user_role': user_role,
                'agent_id': agent_id
            }
        })
        
        # 1. Parse Input
        query = UserQuery(query_text=query_text, user_role=user_role)
        
        # 2. Route Query
        logger.info("Dispatcher analyzing query...")
        
        # Check if agents exist
        from ..api.database import SessionLocal, Agent
        db = SessionLocal()
        try:
            agent_count = db.query(Agent).count()
            if agent_count == 0:
                logger.warning("No agents available in database")
                return {
                    "final_answer": "No agents are available. Please create at least one agent in the Settings page to get started.",
                    "agent_name": "System",
                    "sources": []
                }
        finally:
            db.close()
        
        routing_start = time.time()
        routing = self.dispatcher.route_query(query)
        routing_duration = (time.time() - routing_start) * 1000
        
        log_agent_execution(
            agent_name="dispatcher",
            operation="route_query",
            duration_ms=routing_duration,
            selected_agent=routing.agent_name,
            confidence=routing.confidence,
            reasoning=routing.reasoning
        )

        # 3. Specialist Execution (RAG)
        logger.info(f"Specialist executing", extra={
            'extra_fields': {
                'agent_name': routing.agent_name,
                'agent_id': routing.agent_id
            }
        })
        
        specialist_start = time.time()
        agent_response = self.specialist.generate_response(query, routing, agent_id=routing.agent_id)
        specialist_duration = (time.time() - specialist_start) * 1000
        
        log_agent_execution(
            agent_name="specialist",
            operation="generate_response",
            duration_ms=specialist_duration,
            agent_name_used=routing.agent_name,
            answer_length=len(agent_response.answer),
            sources_count=len(agent_response.sources)
        )

        # 4. Audit
        logger.info("Auditor reviewing response...")
        
        audit_start = time.time()
        audit_result = self.auditor.audit_response(query, agent_response)
        audit_duration = (time.time() - audit_start) * 1000
        
        log_agent_execution(
            agent_name="auditor",
            operation="audit_response",
            duration_ms=audit_duration,
            is_safe=audit_result.is_safe,
            has_feedback=bool(audit_result.feedback)
        )

        # 5. Return Final Result
        total_duration = (time.time() - start_time) * 1000
        
        log_agent_execution(
            agent_name="coordinator",
            operation="process_query_complete",
            duration_ms=total_duration,
            selected_agent=routing.agent_name,
            sources_count=len(agent_response.sources),
            audit_passed=audit_result.is_safe
        )
        
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
