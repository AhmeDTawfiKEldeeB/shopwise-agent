import uuid

import pytest

from Agent.memory.checkpoint import get_checkpointer
from Agent.memory import build_graph
from src.config.settings import get_llm_settings

pytestmark = pytest.mark.skipif(
    not get_llm_settings().groq_api_key,
    reason="LLM_GROQ_API_KEY is not set",
)


@pytest.fixture
def memory_graph():
    return build_graph(threshold=2, recent=2, checkpointer=get_checkpointer())


@pytest.fixture
def thread_id():
    return f"memory-{uuid.uuid4().hex[:8]}"


def ask(graph, thread_id, question):
    result = graph.invoke(
        {"messages": [("human", question)]},
        config={"configurable": {"thread_id": thread_id}},
    )
    return result


class TestSummaryMemory:
    def test_same_thread_restores_conversation_state(self, memory_graph, thread_id):
        secret = uuid.uuid4().hex[:8]

        memory_graph.invoke(
            {"messages": [("human", f"Remember that my favorite number is {secret}. Reply with just: OK")]},
            config={"configurable": {"thread_id": thread_id}},
        )
        result = ask(memory_graph, thread_id, "What is my favorite number? Reply with the number only.")

        assert secret in result["messages"][-1].content

    def test_different_threads_do_not_share_state(self, memory_graph, thread_id):
        other_thread = f"{thread_id}-b"
        secret = uuid.uuid4().hex[:8]

        memory_graph.invoke(
            {"messages": [("human", f"Remember that my favorite number is {secret}. Reply with just: OK")]},
            config={"configurable": {"thread_id": thread_id}},
        )
        state_a = memory_graph.get_state({"configurable": {"thread_id": thread_id}})
        state_b = memory_graph.get_state({"configurable": {"thread_id": other_thread}})

        history_a = " ".join(m.content for m in state_a.values["messages"])
        history_a += state_a.values.get("summary", "")
        assert secret in history_a
        assert state_b.values.get("messages", []) == []

    def test_conversation_is_summarized_after_threshold(self, memory_graph, thread_id):
        for i in range(6):
            memory_graph.invoke(
                {"messages": [("human", f"Just say the word: turn-{i}")]},
                config={"configurable": {"thread_id": thread_id}},
            )

        state = memory_graph.get_state({"configurable": {"thread_id": thread_id}})

        assert state.values["summary"]
        assert len(state.values["messages"]) < 6

    def test_summary_is_persisted_to_postgres(self, thread_id):
        first = build_graph(threshold=2, recent=2, checkpointer=get_checkpointer())
        for i in range(6):
            first.invoke(
                {"messages": [("human", f"Just say the word: turn-{i}")]},
                config={"configurable": {"thread_id": thread_id}},
            )

        second = build_graph(threshold=2, recent=2, checkpointer=get_checkpointer())
        state = second.get_state({"configurable": {"thread_id": thread_id}})

        assert state.values["summary"]

    def test_llm_answers_using_summary(self, memory_graph, thread_id):
        secret = "flamingo"

        memory_graph.invoke(
            {"messages": [("human", f"Remember that my favorite word is {secret}. Reply with just: OK")]},
            config={"configurable": {"thread_id": thread_id}},
        )
        ask(memory_graph, thread_id, "Just say the word: apple")

        state = memory_graph.get_state({"configurable": {"thread_id": thread_id}})
        history = " ".join(m.content for m in state.values["messages"])
        assert secret not in history
        assert secret in state.values["summary"]

        result = ask(memory_graph, thread_id, "Remind me, what is my favorite word? Reply with the word only.")

        assert secret in result["messages"][-1].content.lower()
