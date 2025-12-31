import os
import time
from src.graph import CoachWorkflow
from src.logger import init_log_db, log_execution
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv


load_dotenv()

if "GOOGLE_API_KEY" not in os.environ:
    print("Warning: GOOGLE_API_KEY not found. The LLM calls will fail.")

def run_app():
    # Initialize Log DB
    init_log_db()
    
    print("--- 🎓 AI CAREER & LEARNING COACH (LangGraph) ---")
    user_input = input("Tell me about your Career Goals and Current Skills: ")
    
    # Initialize the Workflow Class
    workflow_app = CoachWorkflow()
    
    # Thread ID allows us to have separate conversations/memories
    session_id = "cli_session_1"
    thread_id = {"configurable": {"thread_id": session_id}}
    
    initial_state = {
        "messages": [HumanMessage(content=user_input)],
        "revision_count": 0,
        "human_feedback": ""
    }

    app = workflow_app.graph
    execution_log = []

    def process_stream(stream_generator):
        """Helper to process the stream and log execution metrics."""
        step_start_time = time.time()
        for event in stream_generator:
            # The stream yields when a node completes.
            step_end_time = time.time()
            duration = step_end_time - step_start_time
            
            for node_name, state_update in event.items():
                timestamp = time.strftime("%H:%M:%S")
                print(f"-> Node '{node_name}' finished in {duration:.2f}s")
                
                # Log to Memory List (for CLI display)
                execution_log.append({
                    "node": node_name,
                    "duration": duration,
                    "timestamp": timestamp
                })
                
                # Log to SQLite
                log_execution(
                    session_id=session_id,
                    node_name=node_name,
                    start_time=step_start_time,
                    end_time=step_end_time,
                    outcome=state_update
                )
            
            # Reset timer for the next node
            step_start_time = time.time()

    # 1. Start execution
    print("\n--- Starting Workflow ---")
    process_stream(app.stream(initial_state, thread_id))

    # 2. Human-in-the-Loop Block
    while True:
        # Check current state at the breakpoint
        snapshot = app.get_state(thread_id)
        
        # If the graph ended, snapshot.next will be empty
        if not snapshot.next:
            print("\nWorkflow Completed.")
            # Print final plan if available
            if "learning_plan" in snapshot.values:
                print("\n--- FINAL APPROVED PLAN ---")
                print(snapshot.values["learning_plan"])
            break

        # We are paused at 'human_review'
        current_plan = snapshot.values.get('learning_plan', 'Generating...')
        
        print(f"\n\n--- PROPOSED LEARNING PLAN ---")
        print(current_plan)
        print("------------------------------------------------")

        feedback = input("\nType 'APPROVE' to finish, or type your feedback to change the plan: ")
        
        # Update state with feedback
        app.update_state(thread_id, {"human_feedback": feedback})
        
        print("\n--- Resuming Workflow ---")
        # Resume execution
        process_stream(app.stream(None, thread_id))

    # 3. Final Execution Log
    print("\n" + "="*50)
    print(" EXECUTION PERFORMANCE LOG")
    print("="*50)
    print(f"{'Order':<6} | {'Node Name':<20} | {'Time (s)':<10} | {'Timestamp':<10}")
    print("-" * 56)
    
    for i, entry in enumerate(execution_log, 1):
        print(f"{i:<6} | {entry['node']:<20} | {entry['duration']:<10.2f} | {entry['timestamp']:<10}")
    
    final_snapshot = app.get_state(thread_id)
    revision_count = final_snapshot.values.get('revision_count', 0)
    
    print("-" * 56)
    print(f"Total Revisions (Iterations): {revision_count}")
    print(f"Final Outcome: {'Approved' if not final_snapshot.next else 'In Progress'}")
    print(f"Logs saved to: execution_logs.sqlite")
    print("="*50)

if __name__ == "__main__":
    run_app()
