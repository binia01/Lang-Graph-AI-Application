import operator
from typing import Annotated, TypedDict, List, Dict, Optional
from langchain_core.messages import BaseMessage

class CoachState(TypedDict):
    """
    Represents the state of our AI Career Coach graph.
    """
    messages: Annotated[List[BaseMessage], operator.add]
    user_profile: Dict[str, str]  
    gap_analysis: str
    learning_plan: str
    human_feedback: str
    revision_count: int
    is_approved: bool
