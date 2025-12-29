import os
from src.graph import TravelWorkflow
from dotenv import load_dotenv

# 1. Load the .env file immediately
load_dotenv()
# --- CONFIGURATION CHECK ---
if "GOOGLE_API_KEY" not in os.environ:
    raise ValueError("Please set the GOOGLE_API_KEY environment variable.")

def run_app():
    print("--- 🌍 AI TRAVEL ASSISTANT (LangGraph) ---")
    location = input("Where do you want to go? (Try 'London' for rain logic): ")
    
    # Initialize the Workflow Class
    workflow_app = TravelWorkflow()
    
    # Thread ID allows us to have separate conversations/memories
    thread_id = {"configurable": {"thread_id": "session_1"}}
    
    initial_state = {
        "location": location,
        "revision_count": 0,
        "messages": [],
        "human_feedback": ""
    }

    # 1. Start execution
    print("\n--- Starting Workflow ---")
    # Iterate through the graph until it hits an interrupt or END
    for event in workflow_app.graph.stream(initial_state, thread_id):
        pass 

    # 2. Human-in-the-Loop Block
    while True:
        # Check current state at the breakpoint
        snapshot = workflow_app.graph.get_state(thread_id)
        
        # If the graph ended, snapshot.next will be empty
        if not snapshot.next:
            print("\nWorkflow Completed.")
            break

        current_itinerary = snapshot.values.get('itinerary', 'Generating...')
        
        print(f"\n\n--- 📝 PROPOSED ITINERARY FOR {location.upper()} ---")
        print(current_itinerary)
        print("------------------------------------------------")

        user_input = input("\nType 'APPROVE' to finish, or type your feedback to change the plan: ")

        if user_input.strip().upper() == "APPROVE":
            print("\n✅ Plan Approved! Enjoy your trip.")
            workflow_app.graph.update_state(thread_id, {"human_feedback": "APPROVE"})
            break 
        else:
            print("\n🔄 Sending feedback to AI...")
            # Inject user feedback into state
            workflow_app.graph.update_state(thread_id, {"human_feedback": user_input})
            
            # Resume graph execution
            for event in workflow_app.graph.stream(None, thread_id):
                pass

if __name__ == "__main__":
    run_app()