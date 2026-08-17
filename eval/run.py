import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_SRC = _REPO / "src"
for _p in (str(_SRC), str(_REPO)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from Agent.tools.retrieval import search_products  # noqa: E402
from eval.metrics import PerQueryMetrics, aggregate_metrics, compute_metrics  # noqa: E402
from eval.tracing import enable_tracing, get_client  # noqa: E402
from langsmith import Client  # noqa: E402
from langsmith.run_helpers import trace  # noqa: E402

# ── env config ──────────────────────────────────────────────────────────


def _env_list_int(name: str, default: list[int]) -> list[int]:
    raw = os.environ.get(name)
    if not raw:
        return default
    return [int(x.strip()) for x in raw.strip("[]").split(",") if x.strip()]


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    return int(raw) if raw else default


def _env_str(name: str, default: str) -> str:
    return os.environ.get(name, default)


# ── dataset ─────────────────────────────────────────────────────────────


def load_dataset(path: str | Path) -> list[dict]:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")
    cases = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            cases.append(
                {"query": rec["query"], "expected_ids": rec.get("expected_ids", [])}
            )
    return cases


# ── pipeline ────────────────────────────────────────────────────────────

_METRIC_KEYS = ("recall", "precision", "hit_rate", "mrr")


def _evaluate_case(
    case: dict,
    ks: list[int],
    limit: int,
    *,
    trace_enabled: bool,
    client: Client | None,
    project: str,
) -> dict:
    inputs = {
        "query": case["query"],
        "expected_ids": case["expected_ids"],
        "k_values": ks,
        "limit": limit,
    }

    if trace_enabled:
        client = client or get_client()
        with trace(
            "retrieval_evaluation",
            run_type="chain",
            inputs=inputs,
            project_name=project,
            client=client,
        ) as rt:
            results = search_products(case["query"], limit=limit)
            actual_ids = [r.payload.get("product_id") if r.payload else None for r in results]
            scores = [r.score for r in results]
            metrics = [compute_metrics(actual_ids, case["expected_ids"], k) for k in ks]
            rt.end(
                outputs={
                    "actual_ids": actual_ids,
                    "scores": scores,
                    "metrics": [m.__dict__ for m in metrics],
                }
            )
            _log_feedback(client, rt.id, metrics)
    else:
        results = search_products(case["query"], limit=limit)
        actual_ids = [r.payload.get("product_id") if r.payload else None for r in results]
        scores = [r.score for r in results]
        metrics = [compute_metrics(actual_ids, case["expected_ids"], k) for k in ks]

    return {
        "query": case["query"],
        "expected_ids": case["expected_ids"],
        "actual_ids": actual_ids,
        "scores": [round(s, 6) for s in scores],
        "metrics": {str(m.k): m.__dict__ for m in metrics},
    }


def _log_feedback(client: Client, run_id, metrics: list[PerQueryMetrics]) -> None:
    for m in metrics:
        for key in _METRIC_KEYS:
            client.create_feedback(run_id, key=f"{key}@{m.k}", score=getattr(m, key))


# ── report ──────────────────────────────────────────────────────────────


def _build_overall(per_query: list[dict], ks: list[int]) -> dict:
    flat = []
    for entry in per_query:
        flat.extend(PerQueryMetrics(**v) for v in entry["metrics"].values())
    overall = aggregate_metrics(flat, ks, num_queries=len(per_query))
    return {str(o.k): o.__dict__ for o in overall}


def _print_report(report: dict) -> None:
    print("=" * 60)
    print("ShopWise Retrieval Evaluation Report")
    print(f"Generated at : {report['generated_at']}")
    print(f"Queries      : {report['num_queries']}")
    print("=" * 60)
    print(f"\n{'K':<4}{'Recall@K':<14}{'Precision@K':<14}{'HitRate@K':<14}{'MRR@K':<10}")
    print("-" * 52)
    for k, m in report["overall"].items():
        print(f"{k:<4}{m['recall']:<14.4f}{m['precision']:<14.4f}{m['hit_rate']:<14.4f}{m['mrr']:<10.4f}")
    for entry in report["per_query"]:
        print(f"\nQuery: {entry['query']}")
        print(f"  expected : {entry['expected_ids']}")
        print(f"  actual   : {entry['actual_ids']}")
        for k, m in entry["metrics"].items():
            print(f"  K={k} recall={m['recall']:.4f} prec={m['precision']:.4f} hit={m['hit_rate']:.4f} mrr={m['mrr']:.4f}")


def _save_report(report: dict, report_dir: str) -> Path:
    report_dir = Path(report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = report_dir / f"report_{ts}.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


# ── CLI ─────────────────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m eval.run",
        description="Evaluate the ShopWise product retrieval pipeline.",
    )
    parser.add_argument("--dataset", default=None)
    parser.add_argument("--k", default=None, help="Comma-separated K values, e.g. '1,3,5'.")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--max-queries", type=int, default=None)
    parser.add_argument("--report-dir", default=None)
    parser.add_argument("--no-trace", action="store_true")
    args = parser.parse_args(argv)

    ks = [int(x) for x in args.k.split(",")] if args.k else _env_list_int("EVAL_K_VALUES", [1, 3, 5])
    limit = args.limit if args.limit is not None else _env_int("EVAL_DEFAULT_LIMIT", 5)
    dataset_path = args.dataset or _env_str("EVAL_DATASET_PATH", "eval/data/eval_queries.jsonl")
    report_dir = args.report_dir or _env_str("EVAL_REPORT_DIR", "eval/reports")
    max_queries = args.max_queries
    trace_enabled = not args.no_trace

    if max(ks) > limit:
        parser.error(f"limit ({limit}) must be >= max(K) ({max(ks)}).")

    dataset = load_dataset(dataset_path)
    print(f"Loaded {len(dataset)} queries from {dataset_path}")
    if max_queries:
        dataset = dataset[:max_queries]

    if trace_enabled:
        client = enable_tracing()
        project = os.environ.get("LANGSMITH_PROJECT", "ShopWise")
        print(f"LangSmith tracing enabled (project={project})")
    else:
        client = None
        project = "ShopWise"

    results = [
        _evaluate_case(c, ks, limit, trace_enabled=trace_enabled, client=client, project=project)
        for c in dataset
    ]

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "config": {"k_values": ks, "limit": limit, "trace_enabled": trace_enabled},
        "num_queries": len(results),
        "per_query": results,
        "overall": _build_overall(results, ks),
    }
    _print_report(report)
    path = _save_report(report, report_dir)
    print(f"\nReport written: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
