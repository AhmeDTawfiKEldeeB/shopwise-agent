from collections.abc import Generator
from functools import lru_cache

from Agent.memory import build_graph


@lru_cache
def build_agent():
    return build_graph()


def ask(question: str, thread_id: str = "default") -> str:
    agent = build_agent()
    result = agent.invoke(
        {"messages": [("human", question)]},
        config={"configurable": {"thread_id": thread_id}},
    )
    return result["messages"][-1].content


def stream(question: str, thread_id: str = "default") -> Generator[str]:
    agent = build_agent()
    for event in agent.astream_events(
        {"messages": [("human", question)]},
        config={"configurable": {"thread_id": thread_id}},
        version="v2",
    ):
        kind = event["event"]
        if kind == "on_chat_model_stream":
            chunk = event["data"].get("chunk")
            if chunk and hasattr(chunk, "content") and chunk.content:
                yield chunk.content
