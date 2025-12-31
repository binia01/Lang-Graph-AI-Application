import streamlit as st
import os
import time
import sqlite3
import uuid
from dotenv import load_dotenv

# Import our modular graph components
from src.graph import CoachWorkflow
from src.logger import init_log_db, log_execution
from langchain_core.messages import HumanMessage

# 1. Load Environment Variables
load_dotenv()

# Initialize DB for logging
init_log_db()

# Page Config
st.set_page_config(page_title="AI Career Coach", page_icon="🎓", layout="wide")

# --- CSS STYLING ---
st.markdown("""
<style>
    .stChatMessage {
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# --- DATABASE HELPERS ---
DB_PATH = "coach_memory.sqlite"

def get_all_threads():
    """Fetches unique thread_ids from the checkpoints table in sqlite."""
    try:
        # We need a read-only connection to find threads
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # LangGraph stores thread_id in the checkpoints table
        cursor.execute("SELECT DISTINCT thread_id FROM checkpoints ORDER BY thread_id DESC")
        threads = [row[0] for row in cursor.fetchall()]
        conn.close()
        return threads
    except sqlite3.OperationalError:
        # Table might not exist yet if app hasn't run
        return []

# --- INITIALIZATION ---
if "workflow" not in st.session_state:
    # Initialize workflow with the shared DB path
    st.session_state.workflow = CoachWorkflow(db_path=DB_PATH)

if "current_thread_id" not in st.session_state:
    # Default to a new random session
    st.session_state.current_thread_id = str(uuid.uuid4())

# --- SIDEBAR: HISTORY ---
with st.sidebar:
    st.title("🗂️ Chat History")
    
    # 1. New Chat Button
    if st.button("➕ New Session", use_container_width=True):
        st.session_state.current_thread_id = str(uuid.uuid4())
        st.rerun()

    st.markdown("---")
    
    # 2. List Existing Threads
    existing_threads = get_all_threads()
    
    # Ensure current thread is in the list so it can be selected
    # This handles the "New Session" case where the ID is not yet in the DB
    all_options = existing_threads.copy()
    if st.session_state.current_thread_id not in all_options:
        all_options.insert(0, st.session_state.current_thread_id)
    
    if all_options:
        st.caption("Conversations")
        
        try:
            index = all_options.index(st.session_state.current_thread_id)
        except ValueError:
            index = 0
            
        selected_thread = st.radio(
            "Select a session:", 
            options=all_options,
            index=index,
            key="thread_selector",
            format_func=lambda x: f"{x[:8]}..." if len(x) > 8 else x
        )
        
        # If user switches selection, update state
        if selected_thread != st.session_state.current_thread_id:
            st.session_state.current_thread_id = selected_thread
            st.rerun()
    else:
        st.info("No past chats found.")

# --- LOAD STATE FROM GRAPH ---
app = st.session_state.workflow.graph
config = {"configurable": {"thread_id": st.session_state.current_thread_id}}

# Get the current state of the selected thread
snapshot = app.get_state(config)

# Extract Messages and Status
if snapshot.values:
    graph_messages = snapshot.values.get("messages", [])
    current_plan = snapshot.values.get("learning_plan")
    
    # Check if we are waiting for human review
    next_node = snapshot.next
    is_awaiting_feedback = "human_review" in next_node if next_node else False
else:
    graph_messages = []
    current_plan = None
    is_awaiting_feedback = False

# --- MAIN UI ---
st.title("🎓 AI Career & Learning Coach")
st.caption(f"Session ID: {st.session_state.current_thread_id}")

if not graph_messages:
    st.write("Tell me about your **Career Goals** and **Current Skills**.")

# 1. Render Chat History
for msg in graph_messages:
    role = "user" if isinstance(msg, HumanMessage) else "assistant"
    with st.chat_message(role):
        st.markdown(msg.content)

# 2. Handle User Input
prompt_label = "Give feedback to adjust plan..." if is_awaiting_feedback else "E.g., I want to be a Data Scientist..."

if user_input := st.chat_input(prompt_label):
    
    # Render user message immediately
    with st.chat_message("user"):
        st.markdown(user_input)

    # Helper for logging
    session_id = st.session_state.current_thread_id
    
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        status_box = st.status("AI is thinking...", expanded=True)
        
        try:
            step_start_time = time.time()
            events = None

            if is_awaiting_feedback:
                # --- FEEDBACK MODE ---
                status_box.write("Applying feedback...")
                # Update state with feedback
                app.update_state(config, {"human_feedback": user_input})
                # Resume execution
                events = app.stream(None, config)
            else:
                # --- NEW INPUT MODE ---
                status_box.write("Starting analysis...")
                events = app.stream({"messages": [HumanMessage(content=user_input)]}, config)

            # Process Events
            for event in events:
                step_end_time = time.time()
                duration = step_end_time - step_start_time
                
                for key, value in event.items():
                    status_box.write(f"Executed: {key}")
                    
                    # Log to SQLite
                    log_execution(
                        session_id=session_id,
                        node_name=key,
                        start_time=step_start_time,
                        end_time=step_end_time,
                        outcome=value
                    )
                    
                    # Display Plan Updates
                    if key == "plan_generator" or key == "plan_refiner":
                        plan = value.get("learning_plan")
                        if plan:
                            message_placeholder.markdown(f"**Generated Plan:**\n\n{plan}")
                    
                    # Display Gap Analysis
                    if key == "gap_analysis":
                         gap = value.get("gap_analysis")
                         with st.expander("Gap Analysis Details"):
                             st.markdown(gap)
                
                step_start_time = time.time()

            # Check final status
            final_snapshot = app.get_state(config)
            if final_snapshot.next:
                if final_snapshot.next[0] == "human_review":
                    status_box.update(label="Waiting for Review", state="running", expanded=False)
                    st.info("The plan is ready for your review. Please provide feedback or type 'Approve' to finish.")
            else:
                status_box.update(label="Complete", state="complete", expanded=False)
                st.success("Plan Approved! Good luck with your learning journey.")
                
            # Force a rerun to update the chat history view properly
            time.sleep(1)
            st.rerun()

        except Exception as e:
            status_box.update(label="Error", state="error")
            st.error(f"An error occurred: {e}")
