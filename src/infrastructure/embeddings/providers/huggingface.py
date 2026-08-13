from sentence_transformers import SentenceTransformer

from src.config.settings import get_embedding_settings
from infrastructure.embeddings.interface import EmbeddingModel


class HuggingFaceEmbeddings(EmbeddingModel):
    def __init__(
        self,
        model_name: str | None = None,
        device: str | None = None,
    ) -> None:
        settings = get_embedding_settings()
        self.model_name = model_name or settings.huggingface_model
        self.device = (device or settings.huggingface_device) or None
        self._model = SentenceTransformer(self.model_name, device=self.device)

    @property
    def model(self) -> SentenceTransformer:
        return self._model

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        embeddings = self._model.encode(
            texts, normalize_embeddings=True, convert_to_numpy=True
        )
        return embeddings.tolist()

    def embed_query(self, text: str) -> list[float]:
        embedding = self._model.encode(
            [text], normalize_embeddings=True, convert_to_numpy=True
        )
        return embedding[0].tolist()

    def get_dimension(self) -> int:
        return self._model.get_sentence_embedding_dimension()

    def close(self) -> None:
        del self._model
