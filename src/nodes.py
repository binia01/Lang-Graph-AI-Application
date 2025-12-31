import os
from typing import Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from src.state import CoachState
from dotenv import load_dotenv

# Load the .env file immediately
load_dotenv()

if "GOOGLE_API_KEY" not in os.environ:
    print("Warning: GOOGLE_API_KEY not found. The LLM calls will fail.")

class CoachNodes:
    """
    Encapsulates the logic for individual nodes in the AI Career Coach graph.
    """
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.7)

    def node_profile_analyzer(self, state: CoachState) -> Dict[str, Any]:
        """
        Node 1: Analyzes the user's initial message to extract career goals and skills.
        """
        print("\n[NODE: Profile Analyzer] Extracting user profile...")
        
        # Get the latest message from the user
        last_message = state["messages"][-1].content
        
        prompt = f"""
        You are an expert career counselor. Analyze the following user input and extract:
        1. Career Goals
        2. Current Skills
        
        User Input: "{last_message}"
        
        Return the response as a JSON-like string or just a structured summary.
        For this internal step, just summarize them clearly.
        """
        
        response = self.llm.invoke([HumanMessage(content=prompt)])
        
        # In a real app, we might parse JSON here. For now, we store the text.
        return {
            "user_profile": {"raw_summary": response.content},
            "messages": [response]
        }

    def node_gap_analyzer(self, state: CoachState) -> Dict[str, Any]:
        """
        Node 2: Identifies the gap between current skills and career goals.
        """
        print("\n[NODE: Gap Analyzer] Analyzing skill gaps...")
        
        profile = state["user_profile"]["raw_summary"]
        
        prompt = f"""
        Based on the following user profile, perform a gap analysis:
        
        {profile}
        
        Identify missing skills, knowledge areas, or experiences required to achieve the career goals.
        """
        
        response = self.llm.invoke([HumanMessage(content=prompt)])
        
        return {
            "gap_analysis": response.content,
            "messages": [response]
        }

    def node_plan_generator(self, state: CoachState) -> Dict[str, Any]:
        """
        Node 3: Generates a learning plan based on the gap analysis.
        """
        print("\n[NODE: Plan Generator] Creating learning plan...")
        
        gap_analysis = state["gap_analysis"]
        
        prompt = f"""
        Create a comprehensive learning plan to bridge the following gaps:
        
        {gap_analysis}
        
        Include:
        1. Recommended courses or resources.
        2. Project ideas.
        3. Timeline estimates.
        """
        
        response = self.llm.invoke([HumanMessage(content=prompt)])
        
        return {
            "learning_plan": response.content,
            "messages": [response],
            "revision_count": state.get("revision_count", 0)
        }

    def node_human_review(self, state: CoachState) -> Dict[str, Any]:
        """
        Node 4: HITL - Pauses execution to wait for human feedback.
        This node doesn't do much processing itself, it just acts as a checkpoint.
        In a real LangGraph setup, we might interrupt *before* this node, 
        but here we use it to process the feedback if it exists.
        """
        print("\n[NODE: Human Review] Processing feedback...")
        
        # If we are here, it means the graph resumed after human input (or it's the first pass).
        # In this design, we check if 'human_feedback' is populated in the state update.
        
        feedback = state.get("human_feedback", "")
        
        if feedback and "approve" in feedback.lower():
            return {"is_approved": True}
        elif feedback:
            return {"is_approved": False}
        else:
            # First pass or no feedback yet, assume we need review
            return {"is_approved": False}

    def node_plan_refiner(self, state: CoachState) -> Dict[str, Any]:
        """
        Node 5: Refines the plan based on human feedback.
        """
        print("\n[NODE: Plan Refiner] Refining plan...")
        
        current_plan = state["learning_plan"]
        feedback = state["human_feedback"]
        
        prompt = f"""
        The user has provided feedback on the learning plan.
        
        Current Plan:
        {current_plan}
        
        User Feedback:
        {feedback}
        
        Please update the plan to address the feedback.
        """
        
        response = self.llm.invoke([HumanMessage(content=prompt)])
        
        return {
            "learning_plan": response.content,
            "messages": [response],
            "revision_count": state["revision_count"] + 1,
            "human_feedback": "" 
        }
