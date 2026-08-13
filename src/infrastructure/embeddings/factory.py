from functools import lru_cache

from src.config.settings import get_embedding_settings
from infrastructure.embeddings.interface import EmbeddingModel
from infrastructure.embeddings.providers import GeminiEmbeddings, HuggingFaceEmbeddings

_PROVIDERS: dict[str, type[EmbeddingModel]] = {}


def register_provider(name: str, provider_cls: type[EmbeddingModel]) -> None:
    _PROVIDERS[name] = provider_cls


class EmbeddingsFactory:
    @staticmethod
    def create(provider: str | None = None, **kwargs) -> EmbeddingModel:
        provider = provider or get_embedding_settings().provider
        if provider not in _PROVIDERS:
            raise ValueError(
                f"Unknown embedding provider '{provider}'. "
                f"Registered providers: {sorted(_PROVIDERS)}"
            )
        return _PROVIDERS[provider](**kwargs)


@lru_cache
def get_embedding_model() -> EmbeddingModel:
    return EmbeddingsFactory.create()


register_provider("huggingface", HuggingFaceEmbeddings)
register_provider("gemini", GeminiEmbeddings)
