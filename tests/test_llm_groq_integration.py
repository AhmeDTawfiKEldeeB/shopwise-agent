import time

import pytest
from openai import RateLimitError

from src.config.settings import get_llm_settings
from infrastructure.llm import ChatMessage
from infrastructure.llm.providers.groq import GroqLLM

pytestmark = pytest.mark.skipif(
    not get_llm_settings().groq_api_key,
    reason="LLM_GROQ_API_KEY is not set",
)

MAX_RETRIES = 5
RETRY_DELAY_SECONDS = 10


@pytest.fixture(autouse=True)
def cleanup_collections():
    yield


def _call_with_retry(fn, *args, **kwargs):
    for attempt in range(MAX_RETRIES):
        try:
            return fn(*args, **kwargs)
        except RateLimitError:
            if attempt == MAX_RETRIES - 1:
                raise
            time.sleep(RETRY_DELAY_SECONDS)


class TestGroqIntegration:
    def test_generate_returns_response(self):
        llm = GroqLLM()
        try:
            assert llm.model == get_llm_settings().groq_model
            result = _call_with_retry(llm.generate, "Reply with exactly: OK")
            print(f"\n[generate] model={llm.model}")
            print(f"[generate] answer: {result}")
            assert result is not None
            assert isinstance(result, str)
            assert result.strip() != ""
        finally:
            llm.close()

    def test_chat_returns_response(self):
        llm = GroqLLM()
        try:
            assert llm.model == get_llm_settings().groq_model
            result = _call_with_retry(
                llm.chat,
                [ChatMessage(role="user", content="who is messi")],
            )
            print(f"\n[chat] model={llm.model}")
            print(f"[chat] answer: {result}")
            assert result is not None
            assert isinstance(result, str)
            assert result.strip() != ""
        finally:
            llm.close()
