from langchain_core.tools import tool

from infrastructure.embeddings import get_embedding_model
from infrastructure.vector_db import get_vector_store
from src.config.settings import get_vector_db_settings


def search_products(query: str, limit: int = 5) -> list:
    """Run the product retrieval pipeline and return scored search results.

    Embeds the query with the configured embedding model and searches the
    configured Qdrant collection. Returns a list of ``SearchResult`` objects
    (with ``id``, ``score``, and ``payload``).

    This is the single implementation used both by the production tool
    (``retrieve_products``) and by the retrieval evaluation pipeline.
    """
    vector = get_embedding_model().embed_query(query)
    return get_vector_store().search(
        get_vector_db_settings().collection, vector, limit=limit
    )


@tool
def retrieve_products(query: str, limit: int = 5) -> list[dict]:
    """Retrieve products from the Qdrant vector store that best match the given query.

    Embeds the query using the configured embedding model, searches the Qdrant
    collection, and returns the top matching products with their details.

    Args:
        query: natural-language description of the product the user is looking for.
        limit: maximum number of products to return (default 5).
    """
    return [result.payload for result in search_products(query, limit=limit)]
