"""Calendar attribution of one continuous episode, including terminal fees."""

from collections import defaultdict
from datetime import date
from typing import Any

import numpy as np

from indexpilot_us100.portfolio.config import SimulationConfig
from indexpilot_us100.portfolio.market import MarketData, decision_indices

from .types import DecisionRecord, FrozenProtocol, Scenario, YearCoverage


def expected_yearly_coverage(
    market: MarketData, simulation: SimulationConfig
) -> dict[int, YearCoverage]:
    """Derive intended per-year intervals before a policy can terminate early."""
    coverage = {}
    for index in decision_indices(market, simulation.risk_window):
        start, end = market.dates[index : index + 2]
        row = coverage.setdefault(end.year, dict(start_date=start, end_date=end))
        row["end_date"] = end
    return coverage


def yearly_summary(
    scenario: Scenario,
    intervals: list[dict[str, Any]],
    decisions: list[DecisionRecord],
    events: list[dict[str, Any]],
    trades: list[dict[str, Any]],
    protocol: FrozenProtocol,
    expected_coverage: dict[int, YearCoverage],
) -> list[dict[str, Any]]:
    if len(intervals) != len(decisions) or len(events) != len(intervals):
        raise ValueError("Yearly interval/decision alignment failed")
    groups = defaultdict(list)
    for interval, decision, event in zip(intervals, decisions, events):
        groups[interval["end_date"].year].append((interval, decision, event))
    start = date.fromisoformat(protocol["evaluation_config"]["test_start"])
    end = date.fromisoformat(protocol["evaluation_config"]["test_end"])
    output = []
    for year, records in sorted(groups.items()):
        first, last = records[0][0]["date"], records[-1][0]["end_date"]
        expected = expected_coverage[year]
        partial = (
            (year == start.year and start > date(year, 1, 1))
            or (year == end.year and end < date(year, 12, 31))
            or first != expected["start_date"]
            or last != expected["end_date"]
        )
        counts = {str(action): 0 for action in (-1.0, -0.5, 0.0, 0.5, 1.0)}
        counts["hold"] = 0
        for _, decision, _ in records:
            target = "hold" if decision["target"] is None else str(decision["target"])
            counts[target] = counts.get(target, 0) + 1
        output.append(
            dict(
                scenario_id=scenario["scenario_id"],
                year=year,
                start_date=first.isoformat(),
                end_date=last.isoformat(),
                interval_count=len(records),
                net_return=float(np.prod([1 + row["net_return"] for row, _, _ in records]) - 1),
                fees=sum(row["fees"] for row, _, _ in records),
                active_intervals=sum(event["holdings"] != 0 for _, _, event in records),
                closed_trades=sum(row["exit_date"].year == year for row in trades),
                partial_year=partial,
                expected_start_date=expected["start_date"].isoformat(),
                expected_end_date=expected["end_date"].isoformat(),
                **{
                    "action_" + key + "_fraction": value / len(records)
                    for key, value in counts.items()
                },
            )
        )
    return output
