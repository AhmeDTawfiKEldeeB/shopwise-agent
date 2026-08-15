import uuid

import pytest

from Agent.agent import ask
from src.config.settings import get_llm_settings

pytestmark = pytest.mark.skipif(
    not get_llm_settings().groq_api_key,
    reason="LLM_GROQ_API_KEY is not set",
)


@pytest.fixture(autouse=True)
def cleanup_collections():
    yield


class TestPostgresCheckpointer:
    def test_same_thread_restores_conversation_state(self):
        thread_id = f"test-{uuid.uuid4().hex[:8]}"
        secret = uuid.uuid4().hex[:8]

        ask(f"Remember that my favorite number is {secret}. Reply with just: OK", thread_id=thread_id)
        answer = ask("What is my favorite number? Reply with the number only.", thread_id=thread_id)

        assert secret in answer

    def test_different_thread_starts_separate_conversation(self):
        thread_a = f"test-a-{uuid.uuid4().hex[:8]}"
        thread_b = f"test-b-{uuid.uuid4().hex[:8]}"
        secret = uuid.uuid4().hex[:8]

        ask(f"Remember that my favorite number is {secret}. Reply with just: OK", thread_id=thread_a)
        answer_b = ask("What is my favorite number? Reply with the number only.", thread_id=thread_b)

        assert secret not in answer_b
