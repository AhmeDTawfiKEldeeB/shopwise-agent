
from infrastructure.vector_db.interface import (
    Distance,
    Filter,
    SearchResult,
    StoredRecord,
    VectorRecord,
)
from infrastructure.vector_db.providers.qdrant import QdrantDB


class TestPing:
    def test_ping_returns_true_for_server_client(self, qdrant_db):
        assert qdrant_db.ping() is True


class TestCollections:
    def test_collection_exists_false_when_absent(self, qdrant_db, collection_name):
        assert qdrant_db.collection_exists(collection_name) is False

    def test_create_collection(self, qdrant_db, collection_name, vector_size):
        qdrant_db.create_collection(collection_name, vector_size)
        assert qdrant_db.collection_exists(collection_name) is True

    def test_create_collection_is_idempotent(self, qdrant_db, collection_name, vector_size):
        qdrant_db.create_collection(collection_name, vector_size)
        qdrant_db.create_collection(collection_name, vector_size)
        assert qdrant_db.collection_exists(collection_name) is True

    def test_create_collection_supports_distance(self, qdrant_db, collection_name, vector_size):
        qdrant_db.create_collection(collection_name + "_cosine", vector_size, distance=Distance.COSINE)
        qdrant_db.create_collection(collection_name + "_dot", vector_size, distance=Distance.DOT)
        qdrant_db.create_collection(collection_name + "_euclid", vector_size, distance=Distance.EUCLID)
        assert qdrant_db.collection_exists(collection_name + "_cosine") is True
        assert qdrant_db.collection_exists(collection_name + "_dot") is True
        assert qdrant_db.collection_exists(collection_name + "_euclid") is True

    def test_ensure_collection_creates_when_missing(self, qdrant_db, collection_name, vector_size):
        created = qdrant_db.ensure_collection(collection_name, vector_size)
        assert created is True
        assert qdrant_db.collection_exists(collection_name) is True

    def test_ensure_collection_skips_when_exists(self, qdrant_db, collection_name, vector_size):
        qdrant_db.create_collection(collection_name, vector_size)
        created = qdrant_db.ensure_collection(collection_name, vector_size)
        assert created is False

    def test_delete_collection(self, qdrant_db, collection_name, vector_size):
        qdrant_db.create_collection(collection_name, vector_size)
        qdrant_db.delete_collection(collection_name)
        assert qdrant_db.collection_exists(collection_name) is False

    def test_delete_missing_collection_does_not_raise(self, qdrant_db, collection_name):
        qdrant_db.delete_collection(collection_name)

    def test_list_collections(self, qdrant_db, collection_name, vector_size):
        qdrant_db.create_collection(collection_name + "_a", vector_size)
        qdrant_db.create_collection(collection_name + "_b", vector_size)
        names = qdrant_db.list_collections()
        assert collection_name + "_a" in names
        assert collection_name + "_b" in names


class TestUpsert:
    def test_upsert_inserts_records(self, qdrant_db, collection_name, vector_size, sample_records):
        qdrant_db.ensure_collection(collection_name, vector_size)
        records = [VectorRecord(**record) for record in sample_records]
        qdrant_db.upsert(collection_name, records)
        assert qdrant_db.count(collection_name) == 3

    def test_upsert_updates_existing(self, qdrant_db, collection_name, vector_size):
        qdrant_db.ensure_collection(collection_name, vector_size)
        qdrant_db.upsert(collection_name, [VectorRecord(id=1, vector=[0.1] * vector_size, payload={"name": "old"})])
        qdrant_db.upsert(collection_name, [VectorRecord(id=1, vector=[0.1] * vector_size, payload={"name": "new"})])
        records = qdrant_db.retrieve(collection_name, [1])
        assert records[0].payload["name"] == "new"
        assert qdrant_db.count(collection_name) == 1

    def test_upsert_empty_list_is_noop(self, qdrant_db, collection_name, vector_size):
        qdrant_db.ensure_collection(collection_name, vector_size)
        qdrant_db.upsert(collection_name, [])
        assert qdrant_db.count(collection_name) == 0


class TestUpsertOne:
    def test_upsert_one_single_record(self, qdrant_db, collection_name, vector_size):
        qdrant_db.ensure_collection(collection_name, vector_size)
        qdrant_db.upsert_one(collection_name, VectorRecord(id=1, vector=[0.1] * vector_size, payload={"name": "a"}))
        assert qdrant_db.count(collection_name) == 1
        assert qdrant_db.retrieve(collection_name, [1])[0].payload["name"] == "a"


class TestUpsertMany:
    def test_upsert_many_batches(self, qdrant_db, collection_name, vector_size):
        qdrant_db.ensure_collection(collection_name, vector_size)
        records = [
            VectorRecord(id=i, vector=[0.1] * vector_size, payload={"name": str(i)})
            for i in range(10)
        ]
        qdrant_db.upsert_many(collection_name, records, batch_size=3)
        assert qdrant_db.count(collection_name) == 10

    def test_upsert_many_batch_size_larger_than_input(self, qdrant_db, collection_name, vector_size):
        qdrant_db.ensure_collection(collection_name, vector_size)
        records = [VectorRecord(id=i, vector=[0.1] * vector_size) for i in range(2)]
        qdrant_db.upsert_many(collection_name, records, batch_size=64)
        assert qdrant_db.count(collection_name) == 2

    def test_upsert_many_default_batch_size(self, qdrant_db, collection_name, vector_size):
        qdrant_db.ensure_collection(collection_name, vector_size)
        records = [VectorRecord(id=i, vector=[0.1] * vector_size) for i in range(100)]
        qdrant_db.upsert_many(collection_name, records)
        assert qdrant_db.count(collection_name) == 100


class TestSearch:
    @staticmethod
    def _seed(qdrant_db, collection_name, vector_size, sample_records):
        qdrant_db.ensure_collection(collection_name, vector_size)
        qdrant_db.upsert(collection_name, [VectorRecord(**record) for record in sample_records])

    def test_search_returns_scored_results(self, qdrant_db, collection_name, vector_size, sample_records):
        self._seed(qdrant_db, collection_name, vector_size, sample_records)
        query_vector = [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0][:vector_size]
        results = qdrant_db.search(collection_name, query_vector, limit=3)
        assert len(results) == 3
        assert all(isinstance(result, SearchResult) for result in results)
        assert results[0].id == 3
        assert results[0].score >= results[-1].score

    def test_search_respects_limit(self, qdrant_db, collection_name, vector_size, sample_records):
        self._seed(qdrant_db, collection_name, vector_size, sample_records)
        results = qdrant_db.search(collection_name, [0.1] * vector_size, limit=2)
        assert len(results) == 2

    def test_search_empty_collection(self, qdrant_db, collection_name, vector_size):
        qdrant_db.ensure_collection(collection_name, vector_size)
        assert qdrant_db.search(collection_name, [0.1] * vector_size) == []

    def test_search_filter_match(self, qdrant_db, collection_name, vector_size, sample_records):
        self._seed(qdrant_db, collection_name, vector_size, sample_records)
        results = qdrant_db.search(collection_name, [0.5] * vector_size, filter=Filter.match("tag", "fruit"))
        assert all(result.payload["tag"] == "fruit" for result in results)

    def test_search_score_threshold(self, qdrant_db, collection_name, vector_size, sample_records):
        self._seed(qdrant_db, collection_name, vector_size, sample_records)
        query_vector = [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0][:vector_size]
        results = qdrant_db.search(collection_name, query_vector, limit=3, score_threshold=0.99)
        assert all(result.score >= 0.99 for result in results)


class TestRetrieve:
    def test_retrieve_by_ids(self, qdrant_db, collection_name, vector_size, sample_records):
        qdrant_db.ensure_collection(collection_name, vector_size)
        qdrant_db.upsert(collection_name, [VectorRecord(**record) for record in sample_records])
        records = qdrant_db.retrieve(collection_name, [1, 3])
        assert isinstance(records[0], StoredRecord)
        assert {record.id for record in records} == {1, 3}

    def test_retrieve_empty_ids(self, qdrant_db, collection_name):
        assert qdrant_db.retrieve(collection_name, []) == []

    def test_retrieve_missing_ids_skipped(self, qdrant_db, collection_name, vector_size):
        qdrant_db.ensure_collection(collection_name, vector_size)
        qdrant_db.upsert_one(collection_name, VectorRecord(id=1, vector=[0.1] * vector_size))
        records = qdrant_db.retrieve(collection_name, [1, 999])
        assert [record.id for record in records] == [1]


class TestDeletePoints:
    def test_delete_by_ids(self, qdrant_db, collection_name, vector_size, sample_records):
        qdrant_db.ensure_collection(collection_name, vector_size)
        qdrant_db.upsert(collection_name, [VectorRecord(**record) for record in sample_records])
        qdrant_db.delete_points(collection_name, ids=[1, 2])
        assert qdrant_db.count(collection_name) == 1

    def test_delete_by_filter(self, qdrant_db, collection_name, vector_size, sample_records):
        qdrant_db.ensure_collection(collection_name, vector_size)
        qdrant_db.upsert(collection_name, [VectorRecord(**record) for record in sample_records])
        qdrant_db.delete_points(collection_name, filter=Filter.match("tag", "fruit"))
        assert qdrant_db.count(collection_name) == 1

    def test_delete_no_ids_or_filter_is_noop(self, qdrant_db, collection_name, vector_size, sample_records):
        qdrant_db.ensure_collection(collection_name, vector_size)
        qdrant_db.upsert(collection_name, [VectorRecord(**record) for record in sample_records])
        qdrant_db.delete_points(collection_name)
        assert qdrant_db.count(collection_name) == 3


class TestCount:
    def test_count_on_missing_collection(self, qdrant_db, collection_name):
        assert qdrant_db.count(collection_name) == 0

    def test_count_exact(self, qdrant_db, collection_name, vector_size, sample_records):
        qdrant_db.ensure_collection(collection_name, vector_size)
        qdrant_db.upsert(collection_name, [VectorRecord(**record) for record in sample_records])
        assert qdrant_db.count(collection_name) == 3

    def test_count_with_filter(self, qdrant_db, collection_name, vector_size, sample_records):
        qdrant_db.ensure_collection(collection_name, vector_size)
        qdrant_db.upsert(collection_name, [VectorRecord(**record) for record in sample_records])
        assert qdrant_db.count(collection_name, filter=Filter.match("tag", "fruit")) == 2


class TestFilterConversion:
    def test_to_qdrant_filter_none(self):
        assert QdrantDB._to_qdrant_filter(None) is None

    def test_to_qdrant_filter_converts_match(self):
        qdrant_filter = QdrantDB._to_qdrant_filter(Filter.match("name", "apple"))
        assert qdrant_filter is not None
        assert qdrant_filter.must[0].key == "name"
