from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from src.nodes import TravelAgentNodes
from src.state import AgentState


class TravelWorkflow:
    """Manages the graph construction, compiling and execution"""

    def __init__(self):
        self.nodes = TravelAgentNodes()
        self.memory = MemorySaver()
        self.graph = self._build_graph()

    def _build_graph(self):
        """Constructs the LangGraph"""

        builder = StateGraph(AgentState)

        # Add nodes
        builder.add_node("planner", self.nodes.node_planner)
        builder.add_node("weather_tool", self.nodes.node_weather_tool)
        builder.add_node("adjuster", self.nodes.node_adjuster)
        builder.add_node("human_review", self.nodes.node_human_review)

        # Define Edges(flow)

        builder.set_entry_point("planner")

        builder.add_edge("planner", "weather_tool")

        builder.add_conditional_edges(
            "weather_tool",
            self._weather_routing_logic,
            {
                "bad_weather": "adjuster",
                "good_weather": "human_review"
            }
        )

        builder.add_edge("adjuster", "human_review")

        builder.add_conditional_edges(
            "human_review",
            self._review_routing_logic,
            {
                "approved": END,
                "rejected": "adjuster"
            }
        )

        return builder.compile(
            checkpointer=self.memory,
            interrupt_before=["human_review"]
        )

    def _weather_routing_logic(self, state: AgentState):
        """Conditional logic based on weather."""
        if "Rainy" in state['weather'] or "Rainy and Cold":
            return "bad_weather"
        return "good_weather"

    def _review_routing_logic(self, state: AgentState):
        """Conditional logic based on user feedback."""
        # If feedback exists and says 'approve', end. Else, retry.
        if state.get("human_feedback") == "APPROVE":
            return "approved"
        return "rejected"
