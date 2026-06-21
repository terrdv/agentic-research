from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: str
    content: str


class RunRequest(BaseModel):
    messages: list[ChatMessage]
    thread_id: str | None = None


class RunResponse(BaseModel):
    messages: list[ChatMessage]
    thread_id: str | None = None
