import os
import sys

# Ensure src is in the python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from server.agents.coordinator import Coordinator

def main():
    print("Welcome to Nexus-Mind CLI Interface")
    print("===================================")
    
    # Check for API Key
    if not os.getenv("OPENAI_API_KEY"):
        print("WARNING: OPENAI_API_KEY not found in environment variables.")
        key = input("Please enter your OpenAI API Key: ").strip()
        if key:
            os.environ["OPENAI_API_KEY"] = key
        else:
            print("No key provided. Exiting.")
            return

    try:
        system = Coordinator()
        
        while True:
            query = input("\nUser Query (or 'q' to quit): ").strip()
            if query.lower() in ['q', 'quit', 'exit']:
                print("Exiting...")
                break
            
            if not query:
                continue
                
            result = system.process_query(query)
            
            print("\n---------- NEXUS RESPONSE ----------")
            print(result["final_answer"])
            print("------------------------------------")
            print(f"Source Dept: {result['department']}")
            if result['sources']:
                print(f"Ref Docs: {result['sources']}")
            if result['audit_feedback']:
                print(f"Audit Note: {result['audit_feedback']}")

    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
