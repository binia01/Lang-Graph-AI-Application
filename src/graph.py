from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3
from src.nodes import CoachNodes
from src.state import CoachState


class CoachWorkflow:
    """Manages the graph construction, compiling and execution"""

    def __init__(self, db_path="coach_memory.sqlite"):
        self.nodes = CoachNodes()
        # Use SQLite for persistence
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.memory = SqliteSaver(self.conn)
        self.graph = self._build_graph()

    def _build_graph(self):
        """Constructs the LangGraph"""

        builder = StateGraph(CoachState)

        # Add nodes
        builder.add_node("profile_analyzer", self.nodes.node_profile_analyzer)
        builder.add_node("gap_analyzer", self.nodes.node_gap_analyzer)
        builder.add_node("plan_generator", self.nodes.node_plan_generator)
        builder.add_node("human_review", self.nodes.node_human_review)
        builder.add_node("plan_refiner", self.nodes.node_plan_refiner)

        # Define Edges (flow)
        builder.set_entry_point("profile_analyzer")

        builder.add_edge("profile_analyzer", "gap_analyzer")
        builder.add_edge("gap_analyzer", "plan_generator")
        builder.add_edge("plan_generator", "human_review")

        # Conditional logic for review
        builder.add_conditional_edges(
            "human_review",
            self._review_routing_logic,
            {
                "approved": END,
                "rejected": "plan_refiner",
                "wait": "human_review"
            }
        )

        builder.add_edge("plan_refiner", "human_review")

        # Compile the graph with memory
        return builder.compile(checkpointer=self.memory, interrupt_before=["human_review"])

    def _review_routing_logic(self, state: CoachState):
        """Determines where to go after human review."""
        if state.get("is_approved"):
            return "approved"
        else:
            return "rejected"
