from functools import lru_cache

from src.config.settings import get_llm_settings
from infrastructure.llm.interface import LLM
from infrastructure.llm.providers import GeminiLLM, GroqLLM, OpenRouterLLM

_PROVIDERS: dict[str, type[LLM]] = {}


def register_provider(name: str, provider_cls: type[LLM]) -> None:
    _PROVIDERS[name] = provider_cls


class LLMFactory:
    @staticmethod
    def create(provider: str | None = None, **kwargs) -> LLM:
        provider = provider or get_llm_settings().provider
        if provider not in _PROVIDERS:
            raise ValueError(
                f"Unknown LLM provider '{provider}'. "
                f"Registered providers: {sorted(_PROVIDERS)}"
            )
        return _PROVIDERS[provider](**kwargs)


@lru_cache
def get_llm() -> LLM:
    return LLMFactory.create()


register_provider("openrouter", OpenRouterLLM)
register_provider("gemini", GeminiLLM)
register_provider("groq", GroqLLM)
