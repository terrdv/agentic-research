from langgraph.graph import END, START, StateGraph

from agent.nodes import (
    planner_node,
    researcher_node,
    synthesizer_node,
    tool_node,
    route_from_planner,
    route_from_researcher,
)
from agent.state import AgentState


def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("planner", planner_node)
    graph.add_node("researcher", researcher_node)
    graph.add_node("tools", tool_node)
    graph.add_node("synthesizer", synthesizer_node)

    graph.add_edge(START, "planner")

    graph.add_conditional_edges(
        "planner",
        route_from_planner,
        {"researcher": "researcher", "synthesizer": "synthesizer"},
    )

    graph.add_conditional_edges(
        "researcher",
        route_from_researcher,
        {"tools": "tools", "planner": "planner"},
    )

    graph.add_edge("tools", "researcher")
    graph.add_edge("synthesizer", END)

    return graph.compile()


graph = build_graph()
