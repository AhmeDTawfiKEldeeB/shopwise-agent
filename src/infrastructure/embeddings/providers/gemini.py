from google import genai

from src.config.settings import get_embedding_settings
from infrastructure.embeddings.interface import EmbeddingModel


class GeminiEmbeddings(EmbeddingModel):
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        dimension: int | None = None,
    ) -> None:
        settings = get_embedding_settings()
        self.api_key = api_key or settings.gemini_api_key
        self.model = model or settings.gemini_model
        self._dimension = dimension or settings.dimension
        self._client = genai.Client(api_key=self.api_key)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        response = self._client.models.embed_content(model=self.model, contents=texts)
        return [embedding.values for embedding in response.embeddings]

    def embed_query(self, text: str) -> list[float]:
        response = self._client.models.embed_content(model=self.model, contents=text)
        return response.embeddings[0].values

    def get_dimension(self) -> int:
        return self._dimension

    def close(self) -> None:
        return None
