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
