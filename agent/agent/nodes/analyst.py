from typing import Literal

from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, SystemMessage
from pydantic import BaseModel, Field

from agent.prompts import ANALYST_PROMPT
from agent.state import AgentState
from config.settings import settings


class ChartDataPoint(BaseModel):
    label: str
    value: float


class ChartSpec(BaseModel):
    chart_type: Literal["bar", "line", "scatter"]
    title: str
    x_label: str
    y_label: str
    data: list[ChartDataPoint]


class AnalystOutput(BaseModel):
    summary: str
    gaps: list[str] = Field(default_factory=list)
    charts: list[ChartSpec] = Field(default_factory=list)


_analyst_llm = ChatOpenAI(
    model=settings.openai_model, api_key=settings.openai_api_key, timeout=60, max_retries=3
).with_structured_output(AnalystOutput)


def analyst_node(state: AgentState) -> AgentState:
    messages = [SystemMessage(content=ANALYST_PROMPT)] + state["messages"]
    analysis: AnalystOutput = _analyst_llm.invoke(messages)

    return {
        "analyst_output": analysis.model_dump(),
        "messages": [AIMessage(content=f"[Analyst] {analysis.summary}")],
    }
