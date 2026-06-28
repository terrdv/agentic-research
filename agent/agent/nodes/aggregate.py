from pydantic import BaseModel
from agent.state import AgentState
from agent.prompts import EVIDENCE_AGGREGATION_PROMPT

_evidence_llm = ChatAnthropic(model=settings.anthropic_model).bind_tools(TOOLS)

def evidence_aggregation_node(state: AgentState) -> AgentState:
    messages = [SystemMessage(content = EVIDENCE_AGGREGATION_PROMPT)] + state["messages"]
    response = _evidence_llm.invoke(messages)
    return {
        "messages": [response]
    }

