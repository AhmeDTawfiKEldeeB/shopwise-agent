from collections.abc import Generator
from functools import lru_cache

from Agent.memory import build_graph
from Agent.memory.checkpoint import get_checkpointer


@lru_cache
def build_agent():
    return build_graph(checkpointer=get_checkpointer())


def ask(question: str, thread_id: str = "default") -> str:
    agent = build_agent()
    result = agent.invoke(
        {"messages": [("human", question)]},
        config={"configurable": {"thread_id": thread_id}},
    )
    return result["messages"][-1].content


def _stream_tokens(agent, question: str, thread_id: str) -> Generator[dict]:
    saw_values = False
    last_was_values = False

    for event in agent.stream_events(
        {"messages": [("human", question)]},
        config={"configurable": {"thread_id": thread_id}},
        version="v3",
    ):
        method = event.get("method", "")
        data = event.get("params", {}).get("data", "")

        if method == "values":
            if saw_values and last_was_values:
                yield {"type": "tool", "name": "Searching products..."}
            last_was_values = True
            saw_values = True
            continue

        last_was_values = False

        if method == "messages" and isinstance(data, tuple):
            inner = data[0]
            ev = inner.get("event", "")
            if ev == "content-block-start":
                yield {"type": "thinking_done"}
            if ev == "content-block-delta":
                text = inner.get("delta", {}).get("text", "")
                if text:
                    yield {"type": "token", "text": text}


async def stream(question: str, thread_id: str = "default") -> Generator[str]:
    import asyncio

    agent = build_agent()
    gen = _stream_tokens(agent, question, thread_id)
    loop = asyncio.get_running_loop()
    while True:
        try:
            event = await loop.run_in_executor(None, next, gen, _SENTINEL)
            if event is _SENTINEL:
                break
            yield event
        except StopIteration:
            break


_SENTINEL = object()
