"""Activity, reward components and event-level drawdown interpretation."""

from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .runner import EvaluatedRun
import numpy as np
from indexpilot_us100.agents.state import ACTIONS
from indexpilot_us100.metrics import drawdown_curve


def drawdown_events(ledger: list[dict[str, Any]]) -> dict[str, Any]:
    values = np.array([row["equity"] for row in ledger], dtype=float)
    dd = drawdown_curve(values)
    trough = int(np.argmax(dd))
    if dd[trough] == 0:
        return dict(
            max_drawdown=0.0,
            peak_sequence=None,
            trough_sequence=None,
            recovery_sequence=None,
            peak_date=None,
            trough_date=None,
            recovery_date=None,
            max_underwater_calendar_days=0,
        )
    peak = int(np.flatnonzero(values[: trough + 1] == np.max(values[: trough + 1]))[-1])
    recovered = np.flatnonzero(values[trough + 1 :] >= values[peak])
    recovery = int(trough + 1 + recovered[0]) if len(recovered) else None
    high = values[0]
    peak_day = ledger[0]["date"]
    max_days = 0
    underwater = False
    for row in ledger:
        if row["equity"] >= high:
            if underwater:
                max_days = max(max_days, (row["date"] - peak_day).days)
            high = row["equity"]
            peak_day = row["date"]
            underwater = False
        else:
            underwater = True
            max_days = max(max_days, (row["date"] - peak_day).days)
    return dict(
        max_drawdown=float(dd[trough]),
        peak_sequence=ledger[peak]["sequence"],
        trough_sequence=ledger[trough]["sequence"],
        recovery_sequence=ledger[recovery]["sequence"] if recovery is not None else None,
        peak_date=ledger[peak]["date"].isoformat(),
        trough_date=ledger[trough]["date"].isoformat(),
        recovery_date=ledger[recovery]["date"].isoformat() if recovery is not None else None,
        max_underwater_calendar_days=max_days,
    )


def policy_diagnostics(run: "EvaluatedRun") -> dict[str, Any]:
    result = run.result
    decisions = run.decisions
    count = len(result.intervals)
    events = [row for row in result.ledger if row["kind"] in ("execution", "hold")]
    if len(decisions) != count or len(events) != count:
        raise ValueError("Decision/accounting interval alignment failed")
    exposures = [
        event["holdings"] * event["price"] / interval["start_equity"]
        for event, interval in zip(events, result.intervals)
    ]
    targets = [row["target"] for row in decisions]
    counts = {str(action): sum(value == action for value in targets) for action in ACTIONS}
    counts["hold"] = sum(value is None for value in targets)
    flat = counts["0.0"] / count
    unseen = (
        float(sum(run.agent.visits[row["state"]].sum() == 0 for row in decisions) / count)
        if run.agent is not None
        else None
    )
    durations = [(trade["exit_date"] - trade["entry_date"]).days for trade in result.trades]
    flags = []
    if not durations:
        flags.append("no_trades")
    elif len(durations) < 5:
        flags.append("sparse_trades")
    if flat >= 0.95:
        flags.append("mostly_flat")
    if unseen is not None and unseen > 0:
        flags.append("unseen_states_present")
    if result.status == "insolvent":
        flags.append("insolvent")
    return dict(
        action_counts=counts,
        action_fractions={key: value / count for key, value in counts.items()},
        flat_decision_fraction=flat,
        active_intervals=sum(event["holdings"] != 0 for event in events),
        long_intervals=sum(event["holdings"] > 0 for event in events),
        short_intervals=sum(event["holdings"] < 0 for event in events),
        mean_gross_exposure=float(np.mean(np.abs(exposures))),
        max_gross_exposure=float(np.max(np.abs(exposures))),
        unseen_state_fraction=unseen,
        mean_trade_duration_days=float(np.mean(durations)) if durations else None,
        max_trade_duration_days=max(durations) if durations else None,
        gross_return_sum=sum(row["gross_return"] for row in result.intervals),
        cost_fraction_sum=sum(row["cost_fraction"] for row in result.intervals),
        risk_penalty_sum=result.config.risk_lambda * sum(row["risk"] for row in result.intervals),
        reward_sum=sum(row["reward"] for row in result.intervals),
        drawdown=drawdown_events(result.ledger),
        flags=flags,
    )
