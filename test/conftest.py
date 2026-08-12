import uuid

import pytest

from src.vector_db.providers.qdrant import QdrantDB


@pytest.fixture
def qdrant_db():
    db = QdrantDB()
    yield db
    db.close()


@pytest.fixture
def collection_name():
    return f"test_{uuid.uuid4().hex[:8]}"


@pytest.fixture(autouse=True)
def cleanup_collections(qdrant_db, collection_name):
    yield
    qdrant_db.delete_collection(collection_name)


@pytest.fixture
def vector_size():
    return 8


@pytest.fixture
def sample_records(vector_size):
    return [
        {
            "id": 1,
            "vector": [0.9, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0][:vector_size],
            "payload": {"name": "apple", "tag": "fruit"},
        },
        {
            "id": 2,
            "vector": [0.5, 0.5, 0.5, 0.5, 0.0, 0.0, 0.0, 0.0][:vector_size],
            "payload": {"name": "carrot", "tag": "vegetable"},
        },
        {
            "id": 3,
            "vector": [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0][:vector_size],
            "payload": {"name": "banana", "tag": "fruit"},
        },
    ]