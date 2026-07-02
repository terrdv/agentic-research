from typing import Literal

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage

from agent.prompts import EVIDENCE_AGGREGATION_PROMPT
from agent.state import AgentState
from agent.tools import TOOLS
from config.settings import settings

_evidence_llm = ChatOpenAI(
    model=settings.openai_model, api_key=settings.openai_api_key, timeout=60, max_retries=3
).bind_tools(TOOLS)


def evidence_aggregation_node(state: AgentState) -> AgentState:
    messages = [SystemMessage(content=EVIDENCE_AGGREGATION_PROMPT)] + state["messages"]
    response = _evidence_llm.invoke(messages)
    return {"messages": [response]}

def route_from_evidence_aggregation(state: AgentState) -> Literal["tools", "analyst"]:
    """Conditional edge out of evidence aggregation: run pending tool calls, else analyze."""
    last = state["messages"][-1]
    return "tools" if getattr(last, "tool_calls", None) else "analyst"