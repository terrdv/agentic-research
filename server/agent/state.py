from typing import Annotated
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    task_type: str        # "search" | "read_paper" | "synthesize"
    next_action: str      # "researcher" | "synthesizer" | "end"
    iteration: int
    max_iterations: int
