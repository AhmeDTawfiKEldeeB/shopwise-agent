from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix="APP_",
    )

    name: str = "ShopWise Agent API"
    version: str = "v1"
    debug: bool = False
    api_prefix: str = "/api/v1"


class QdrantSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix="QDRANT_",
    )

    url: str = "http://localhost:6333"
    api_key: str | None = None
    https: bool = False
    prefer_grpc: bool = False
    timeout: float = 5.0


class VectorDbSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix="VECTOR_DB_",
    )

    provider: str = "qdrant"
    collection: str = "default"


@lru_cache
def get_app_settings() -> AppSettings:
    return AppSettings()


@lru_cache
def get_qdrant_settings() -> QdrantSettings:
    return QdrantSettings()


@lru_cache
def get_vector_db_settings() -> VectorDbSettings:
    return VectorDbSettings()