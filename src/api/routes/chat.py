import json
import uuid

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from src.api.schemas.base import ErrorResponse
from src.api.schemas.chat import (
    ChatMessage,
    ChatRequest,
    ThreadHistoryResponse,
    ThreadListResponse,
    ThreadSummary,
)

router = APIRouter(
    prefix="/api/v1",
    tags=["chat"],
)


@router.post("/chat", response_class=StreamingResponse, responses={400: {"model": ErrorResponse}})
async def send_message(req: ChatRequest) -> StreamingResponse:
    from Agent.agent import stream

    thread_id = req.thread_id or f"api-chat-{uuid.uuid4().hex[:8]}"

    def _generate():
        for token in stream(req.message, thread_id=thread_id):
            yield f"data: {json.dumps({'token': token, 'thread_id': thread_id})}\n\n"
        yield f"data: {json.dumps({'done': True, 'thread_id': thread_id})}\n\n"

    return StreamingResponse(_generate(), media_type="text/event-stream")


@router.get("/threads", response_model=ThreadListResponse)
async def list_threads() -> ThreadListResponse:
    from Agent.memory.checkpoint import get_checkpointer

    checkpointer = get_checkpointer()
    seen: dict[str, ThreadSummary] = {}

    for cp in checkpointer.list(None):
        tid = cp.config["configurable"]["thread_id"]
        if tid in seen:
            continue
        messages = cp.checkpoint.get("channel_values", {}).get("messages", [])
        summary = cp.checkpoint.get("channel_values", {}).get("summary", "")
        seen[tid] = ThreadSummary(
            thread_id=tid,
            title=_derive_title(messages, tid),
            summary=summary,
            message_count=len(messages),
        )

    return ThreadListResponse(
        status="success",
        message=f"Found {len(seen)} threads",
        data=list(seen.values()),
    )


@router.get(
    "/threads/{thread_id}/history",
    response_model=ThreadHistoryResponse,
    responses={404: {"model": ErrorResponse}},
)
async def thread_history(thread_id: str) -> ThreadHistoryResponse:
    from Agent.agent import build_agent

    agent = build_agent()
    state = agent.get_state({"configurable": {"thread_id": thread_id}})
    if not state or not state.values:
        return ThreadHistoryResponse(
            status="error",
            message=f"Thread {thread_id!r} not found",
            data=[],
        )

    messages = state.values.get("messages", [])
    history = []
    for msg in messages:
        if msg.type in ("human", "ai") and msg.content:
            history.append(ChatMessage(role="user" if msg.type == "human" else "assistant", content=msg.content))

    return ThreadHistoryResponse(
        status="success",
        message=f"Thread {thread_id!r} history",
        data=history,
    )


def _derive_title(messages, thread_id: str) -> str:
    for msg in messages:
        if getattr(msg, "type", "") == "human" and msg.content:
            text = msg.content.strip()
            return text[:40] + ("…" if len(text) > 40 else "")
    return thread_id
