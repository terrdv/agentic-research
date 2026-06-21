from fastapi import APIRouter
from langchain_core.messages import HumanMessage, AIMessage

from agent.graph import graph
from api.schemas import RunRequest, RunResponse, ChatMessage

router = APIRouter(prefix="/agent", tags=["agent"])


def _to_lc_message(msg: ChatMessage):
    if msg.role == "user":
        return HumanMessage(content=msg.content)
    return AIMessage(content=msg.content)


@router.post("/run", response_model=RunResponse)
async def run_agent(body: RunRequest) -> RunResponse:
    lc_messages = [_to_lc_message(m) for m in body.messages]
    result = await graph.ainvoke({"messages": lc_messages})
    output = [
        ChatMessage(
            role="assistant" if isinstance(m, AIMessage) else "user",
            content=m.content if isinstance(m.content, str) else str(m.content),
        )
        for m in result["messages"]
    ]
    return RunResponse(messages=output, thread_id=body.thread_id)
