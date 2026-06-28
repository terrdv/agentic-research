from langgraph.graph import END, START, StateGraph

from agent.nodes import (
    analyst_node,
    evidence_aggregation_node,
    planner_node,
    synthesizer_node,
    tool_node,
    route_from_planner,
    route_from_evidence_aggregation,
)
from agent.state import AgentState


def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("planner", planner_node)
    graph.add_node("evidence_aggregation", evidence_aggregation_node)
    graph.add_node("analyst", analyst_node)
    graph.add_node("tools", tool_node)
    graph.add_node("synthesizer", synthesizer_node)

    graph.add_edge(START, "planner")

    graph.add_conditional_edges(
        "planner",
        route_from_planner,
        {"evidence_aggregation": "evidence_aggregation", "synthesizer": "synthesizer"},
    )

    graph.add_conditional_edges(
        "evidence_aggregation",
        route_from_evidence_aggregation,
        {"tools": "tools", "analyst": "analyst"},
    )

    graph.add_edge("tools", "evidence_aggregation")
    graph.add_edge("analyst", "planner")
    graph.add_edge("synthesizer", END)

    return graph.compile()


graph = build_graph()
