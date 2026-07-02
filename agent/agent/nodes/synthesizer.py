from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage

from agent.prompts import SYNTHESIZER_PROMPT
from agent.state import AgentState
from config.settings import settings

_synthesizer_llm = ChatOpenAI(
    model=settings.openai_model, api_key=settings.openai_api_key, timeout=60, max_retries=3
)


def synthesizer_node(state: AgentState) -> AgentState:
    citation_style = state.get("citation_style") or "APA"
    prompt = SYNTHESIZER_PROMPT.format(citation_style=citation_style)
    messages = [SystemMessage(content=prompt)] + state["messages"]
    response = _synthesizer_llm.invoke(messages)
    return {"messages": [response]}
