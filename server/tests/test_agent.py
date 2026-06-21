import pytest
from langchain_core.messages import HumanMessage

from agent.graph import build_graph
from agent.state import AgentState


@pytest.fixture
def agent_graph():
    return build_graph()


def test_graph_compiles(agent_graph):
    assert agent_graph is not None


@pytest.mark.asyncio
async def test_agent_responds(agent_graph):
    state: AgentState = {"messages": [HumanMessage(content="Hello, who are you?")]}
    result = await agent_graph.ainvoke(state)
    assert len(result["messages"]) > 0
