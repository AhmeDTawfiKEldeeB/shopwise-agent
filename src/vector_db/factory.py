from functools import lru_cache

from src.config.settings import get_vector_db_settings
from src.vector_db.interface import VectorStore
from src.vector_db.providers import QdrantDB

_PRODUCTS: dict[str, type[VectorStore]] = {}


def register_provider(name: str, provider_cls: type[VectorStore]) -> None:
    _PRODUCTS[name] = provider_cls


class VectorStoreFactory:
    @staticmethod
    def create(provider: str | None = None, **kwargs) -> VectorStore:
        provider = provider or get_vector_db_settings().provider
        if provider not in _PRODUCTS:
            raise ValueError(
                f"Unknown vector store provider '{provider}'. "
                f"Registered providers: {sorted(_PRODUCTS)}"
            )
        return _PRODUCTS[provider](**kwargs)


@lru_cache
def get_vector_store() -> VectorStore:
    return VectorStoreFactory.create()


register_provider("qdrant", QdrantDB)