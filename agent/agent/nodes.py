from typing import Literal

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel

from agent.prompts import PLANNER_PROMPT, RESEARCHER_PROMPT, SYNTHESIZER_PROMPT
from agent.state import AgentState
from agent.tools import TOOLS
from config.settings import settings


class PlannerDecision(BaseModel):
    action: Literal["search", "read_paper", "synthesize"]
    reasoning: str


_planner_llm = ChatOllama(model=settings.ollama_model).with_structured_output(PlannerDecision)




_ACTION_TO_NEXT = {
    "search": "researcher",
    "read_paper": "researcher",
    "synthesize": "synthesizer",
}


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


def researcher_node(state: AgentState) -> AgentState:
    task_type = state.get("task_type", "search")
    llm = _reader_llm if task_type == "read_paper" else _researcher_llm
    messages = [SystemMessage(content=RESEARCHER_PROMPT)] + state["messages"]
    response = llm.invoke(messages)
    return {"messages": [response]}


def synthesizer_node(state: AgentState) -> AgentState:
    messages = [SystemMessage(content=SYNTHESIZER_PROMPT)] + state["messages"]
    response = _synthesizer_llm.invoke(messages)
    return {"messages": [response]}


def route_from_planner(state: AgentState) -> str:
    return state["next_action"]


def route_from_researcher(state: AgentState) -> str:
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tools"
    return "planner"


tool_node = ToolNode(TOOLS)
