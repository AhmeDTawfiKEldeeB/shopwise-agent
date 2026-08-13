from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Distance(str, Enum):
    COSINE = "cosine"
    DOT = "dot"
    EUCLID = "euclid"


@dataclass
class VectorRecord:
    id: str | int
    vector: list[float]
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchResult:
    id: str | int
    score: float
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class StoredRecord:
    id: str | int
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class Filter:
    must: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def match(cls, field: str, value: Any) -> "Filter":
        return cls(must=[{"field": field, "match": value}])


class VectorStore(ABC):
    @abstractmethod
    def ping(self, timeout: float = 5.0) -> bool:
        raise NotImplementedError

    @abstractmethod
    def collection_exists(self, collection_name: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def create_collection(
        self,
        collection_name: str,
        vector_size: int,
        distance: Distance = Distance.COSINE,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def ensure_collection(
        self,
        collection_name: str,
        vector_size: int,
        distance: Distance = Distance.COSINE,
    ) -> bool:
        raise NotImplementedError

    @abstractmethod
    def delete_collection(self, collection_name: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def upsert(self, collection_name: str, records: list[VectorRecord]) -> None:
        raise NotImplementedError

    @abstractmethod
    def upsert_one(self, collection_name: str, record: VectorRecord) -> None:
        raise NotImplementedError

    @abstractmethod
    def upsert_many(
        self,
        collection_name: str,
        records: list[VectorRecord],
        batch_size: int = 64,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def search(
        self,
        collection_name: str,
        query_vector: list[float],
        limit: int = 10,
        filter: Filter | None = None,
        score_threshold: float | None = None,
    ) -> list[SearchResult]:
        raise NotImplementedError

    @abstractmethod
    def retrieve(
        self,
        collection_name: str,
        ids: list[str | int],
    ) -> list[StoredRecord]:
        raise NotImplementedError

    @abstractmethod
    def delete_points(
        self,
        collection_name: str,
        ids: list[str | int] | None = None,
        filter: Filter | None = None,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def count(
        self,
        collection_name: str,
        filter: Filter | None = None,
        exact: bool = True,
    ) -> int:
        raise NotImplementedError

    @abstractmethod
    def list_collections(self) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        raise NotImplementedError