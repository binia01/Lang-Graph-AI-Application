import operator
from typing import Annotated, TypedDict, List
from langchain_core.messages import  BaseMessage

class AgentState(TypedDict):
    """
    Represents the state of our graph.
    """
    messages: Annotated[List[BaseMessage], operator.add]
    location: str
    weather: str
    itinerary: str
    human_feedback: str
    revision_count: int