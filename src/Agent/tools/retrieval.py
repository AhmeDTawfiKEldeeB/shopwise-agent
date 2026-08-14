from langchain_core.tools import tool

from infrastructure.embeddings import get_embedding_model
from infrastructure.vector_db import get_vector_store
from src.config.settings import get_vector_db_settings


@tool
def retrieve_products(query: str, limit: int = 5) -> list[dict]:
    """Retrieve products from the Qdrant vector store that best match the given query.

    Embeds the query using the configured embedding model, searches the Qdrant
    collection, and returns the top matching products with their details.

    Args:
        query: natural-language description of the product the user is looking for.
        limit: maximum number of products to return (default 5).
    """
    vector = get_embedding_model().embed_query(query)
    results = get_vector_store().search(
        get_vector_db_settings().collection, vector, limit=limit
    )
    return [result.payload for result in results]
