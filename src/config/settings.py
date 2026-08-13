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


class EmbeddingSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix="EMBEDDING_",
    )

    provider: str = "huggingface"
    dimension: int = 384
    huggingface_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    huggingface_device: str | None = None
    gemini_model: str = "text-embedding-004"
    gemini_api_key: str | None = None


class LLMSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix="LLM_",
    )

    provider: str = "openrouter"
    openrouter_model: str = "openrouter/auto"
    openrouter_api_key: str | None = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    gemini_model: str = "gemini-2.5-flash"
    gemini_api_key: str | None = None
    groq_model: str = "llama-3.3-70b-versatile"
    groq_api_key: str | None = None
    groq_base_url: str = "https://api.groq.com/openai/v1"


class PostgresSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix="POSTGRES_",
    )

    host: str = "localhost"
    port: int = 5432
    user: str = "postgres"
    password: str = "postgres"
    db: str = "shopwise"

    @property
    def database_url(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"


@lru_cache
def get_app_settings() -> AppSettings:
    return AppSettings()


@lru_cache
def get_qdrant_settings() -> QdrantSettings:
    return QdrantSettings()


@lru_cache
def get_vector_db_settings() -> VectorDbSettings:
    return VectorDbSettings()


@lru_cache
def get_postgres_settings() -> PostgresSettings:
    return PostgresSettings()


@lru_cache
def get_embedding_settings() -> EmbeddingSettings:
    return EmbeddingSettings()


@lru_cache
def get_llm_settings() -> LLMSettings:
    return LLMSettings()