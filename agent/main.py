"""Stdio entry point for the Electron main process.

Protocol:
  stdin:  one JSON object per line — {"query": "...", "max_iterations": 5}
  stdout: one JSON event per line (flushed immediately)
    {"type": "node_start", "node": "planner"}
    {"type": "message",    "node": "planner",  "content": "..."}
    {"type": "done"}
    {"type": "error",      "message": "..."}
"""

import json
import sys

from langchain_core.messages import HumanMessage

from agent.graph import graph


def _emit(obj: dict) -> None:
    print(json.dumps(obj), flush=True)


def run_query(query: str, max_iterations: int = 5) -> None:
    initial_state = {
        "messages": [HumanMessage(content=query)],
        "task_type": "search",
        "next_action": "researcher",
        "iteration": 0,
        "max_iterations": max_iterations,
    }

    for chunk in graph.stream(initial_state, stream_mode="updates"):
        for node_name, updates in chunk.items():
            _emit({"type": "node_start", "node": node_name})
            for msg in updates.get("messages", []):
                content = msg.content if hasattr(msg, "content") else str(msg)
                if content:
                    _emit({"type": "message", "node": node_name, "content": content})

    _emit({"type": "done"})


def main() -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            query = req["query"]
            max_iterations = int(req.get("max_iterations", 5))
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            _emit({"type": "error", "message": f"Bad request: {e}"})
            continue

        try:
            run_query(query, max_iterations)
        except Exception as e:
            _emit({"type": "error", "message": str(e)})


if __name__ == "__main__":
    main()
