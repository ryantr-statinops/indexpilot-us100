"""Finite-only seed statistics with explicit missing/infinite/run counts."""

from typing import Any
from .types import ScoreRow
from collections import defaultdict
import numpy as np

METRICS = (
    "net_return",
    "sharpe",
    "max_drawdown",
    "cagr",
    "profit_factor",
    "calmar",
    "total_fees",
    "trade_count",
    "active_intervals",
)


def aggregate_seed_results(rows: list[ScoreRow]) -> list[dict[str, Any]]:
    groups = defaultdict(list)
    for row in rows:
        if row["kind"] != "deterministic":
            groups[(row["kind"], row["policy"], row["risk_lambda"], row["cost_bps"])].append(row)
    output = []
    for (kind, policy, risk_lambda, cost), samples in sorted(groups.items()):
        if len({row["seed"] for row in samples}) != len(samples):
            raise ValueError("Duplicate seed in aggregation")
        for metric in METRICS:
            values = [
                float(row[metric])
                for row in samples
                if row.get(metric) is not None and np.isfinite(row[metric])
            ]
            statuses = [
                row.get(
                    metric + "_status", "finite" if row.get(metric) is not None else "undefined"
                )
                for row in samples
            ]
            output.append(
                dict(
                    kind=kind,
                    policy=policy,
                    risk_lambda=risk_lambda,
                    cost_bps=cost,
                    metric=metric,
                    seed_count=len(samples),
                    finite_count=len(values),
                    undefined_count=statuses.count("undefined"),
                    infinite_count=statuses.count("positive_infinity"),
                    not_applicable_count=statuses.count("not_applicable"),
                    insolvent_count=sum(row["status"] == "insolvent" for row in samples),
                    mean=float(np.mean(values)) if values else None,
                    median=float(np.median(values)) if values else None,
                    sample_std=float(np.std(values, ddof=1)) if len(values) > 1 else None,
                    minimum=min(values) if values else None,
                    maximum=max(values) if values else None,
                )
            )
    return output
