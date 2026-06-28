from typing import Annotated, Optional
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    task_type: str           # "search" | "read_paper" | "synthesize"
    next_action: str         # "evidence_aggregation" | "synthesizer"
    iteration: int
    max_iterations: int
    analyst_output: Optional[dict]  # serialized AnalystOutput, set by analyst_node
