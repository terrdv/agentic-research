from typing import Literal

from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, SystemMessage
from pydantic import BaseModel

from agent.prompts import PLANNER_PROMPT
from agent.state import AgentState
from config.settings import settings


class PlannerDecision(BaseModel):
    action: Literal["search", "read_paper", "synthesize"]
    reasoning: str


_ACTION_TO_NEXT = {
    "search": "evidence_aggregation",
    "read_paper": "evidence_aggregation",
    "synthesize": "synthesizer",
}

_planner_llm = ChatOpenAI(
    model=settings.openai_model, api_key=settings.openai_api_key, timeout=60, max_retries=3
).with_structured_output(PlannerDecision)


def planner_node(state: AgentState) -> AgentState:
    iteration = state.get("iteration", 0)
    max_iter = state.get("max_iterations", 5)

    if iteration >= max_iter:
        return {"next_action": "synthesizer", "task_type": "synthesize", "iteration": iteration}

    messages = [SystemMessage(content=PLANNER_PROMPT)] + state["messages"]
    decision: PlannerDecision = _planner_llm.invoke(messages)

    return {
        "next_action": _ACTION_TO_NEXT[decision.action],
        "task_type": decision.action,
        "iteration": iteration + 1,
        "messages": [AIMessage(content=f"[Planner] {decision.reasoning}")],
    }


def route_from_planner(state: AgentState) -> Literal["evidence_aggregation", "synthesizer"]:
    """Conditional edge out of the planner: follow the branch the planner chose."""
    return state["next_action"]
