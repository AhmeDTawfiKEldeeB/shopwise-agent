import pytest

from Agent.tools.retrieval import retrieve_products
from src.config.settings import get_llm_settings

pytestmark = pytest.mark.skipif(
    not get_llm_settings().groq_api_key,
    reason="LLM_GROQ_API_KEY is not set",
)


class TestRetrieval:
    def test_retrieve_tool_queries_qdrant(self):
        res = retrieve_products.invoke({"query": "cheap wireless headphones", "limit": 3})
        print("\n=== Retrieved from Qdrant ===")
        for item in res:
            print(f"- {item.get('name')} | {item.get('brand')} | {item.get('price')} {item.get('currency')}")
        assert isinstance(res, list)
        assert len(res) >= 1
        assert all(isinstance(item, dict) for item in res)
        assert "name" in res[0]

    def test_retrieve_tool_respects_limit(self):
        res = retrieve_products.invoke({"query": "shampoo", "limit": 2})
        print(f"\n=== count returned: {len(res)} (limit=2) ===")
        for item in res:
            print(f"- {item.get('name')}")
        assert isinstance(res, list)
        assert len(res) <= 2

    def test_agent_answers_with_retrieved_data(self):
        from Agent.agent import ask

        answer = ask("find me a shampoo for dry hair")
        print(f"\n=== Agent answer ===\n{answer}")
        assert isinstance(answer, str)
        assert answer.strip() != ""
