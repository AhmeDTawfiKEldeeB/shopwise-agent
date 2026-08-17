from pydantic import BaseModel, Field

from src.api.schemas.base import StandardResponse


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User message to the agent")
    thread_id: str | None = Field(None, description="Existing thread ID; omit to start a new thread")


class ChatReply(BaseModel):
    reply: str = Field(..., description="Agent's response")
    thread_id: str = Field(..., description="Thread ID for continuing the conversation")


class ChatResponse(StandardResponse[ChatReply]):
    data: ChatReply


class ThreadSummary(BaseModel):
    thread_id: str = Field(..., description="Unique thread identifier")
    title: str = Field("", description="Auto-generated thread title")
    summary: str = Field("", description="Conversation summary if available")
    message_count: int = Field(0, description="Number of messages in the thread")


class ThreadListResponse(StandardResponse[list[ThreadSummary]]):
    data: list[ThreadSummary]


class ChatMessage(BaseModel):
    role: str = Field(..., description="'user' or 'assistant'")
    content: str = Field(..., description="Message content")


class ThreadHistoryResponse(StandardResponse[list[ChatMessage]]):
    data: list[ChatMessage]
