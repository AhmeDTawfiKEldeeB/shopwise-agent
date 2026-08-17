from dataclasses import dataclass


@dataclass
class PerQueryMetrics:
    k: int
    recall: float
    precision: float
    hit_rate: float
    mrr: float


@dataclass
class OverallMetrics:
    k: int
    recall: float
    precision: float
    hit_rate: float
    mrr: float
    num_queries: int


def compute_metrics(
    actual_ids: list[str],
    expected_ids: list[str],
    k: int,
) -> PerQueryMetrics:
    """Compute recall@K, precision@K, hit rate@K (binary) and MRR@K for one query."""
    expected = set(expected_ids)
    retrieved = actual_ids[:k]
    relevant = sum(1 for product_id in retrieved if product_id in expected)

    recall = relevant / len(expected) if expected else 0.0
    precision = relevant / len(retrieved) if retrieved else 0.0
    hit_rate = 1.0 if relevant > 0 else 0.0

    mrr = 0.0
    for rank, product_id in enumerate(retrieved, start=1):
        if product_id in expected:
            mrr = 1.0 / rank
            break

    return PerQueryMetrics(
        k=k,
        recall=recall,
        precision=precision,
        hit_rate=hit_rate,
        mrr=mrr,
    )


def aggregate_metrics(
    per_query: list[PerQueryMetrics],
    ks: list[int],
    num_queries: int,
) -> list[OverallMetrics]:
    """Average per-query metrics over the dataset, grouped by K."""
    overall: list[OverallMetrics] = []
    for k in ks:
        group = [m for m in per_query if m.k == k]
        if not group:
            continue
        overall.append(
            OverallMetrics(
                k=k,
                recall=_mean(m.recall for m in group),
                precision=_mean(m.precision for m in group),
                hit_rate=_mean(m.hit_rate for m in group),
                mrr=_mean(m.mrr for m in group),
                num_queries=num_queries,
            )
        )
    return overall


def _mean(values) -> float:
    values = list(values)
    return sum(values) / len(values) if values else 0.0
