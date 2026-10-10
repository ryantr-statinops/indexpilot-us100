from dataclasses import asdict

import pytest
from test_simulator import market

from indexpilot_us100.evaluation.final import EvaluationConfig
from indexpilot_us100.evaluation.final.diagnostics import policy_diagnostics
from indexpilot_us100.evaluation.final.runner import evaluate_baseline
from indexpilot_us100.portfolio import SimulationConfig


def test_activity_is_not_previous_exposure():
    protocol = {
        "evaluation_config": asdict(EvaluationConfig()),
        "simulation_config": asdict(SimulationConfig()),
    }
    base = dict(kind="deterministic", seed=42, risk_lambda=2.0, cost_bps=10.0)
    cash = evaluate_baseline(protocol, market(), {**base, "policy": "cash"})
    diag = policy_diagnostics(cash)
    assert diag["flat_decision_fraction"] == 1 and diag["active_intervals"] == 0
    assert diag["flags"] == ["no_trades", "mostly_flat"]
    held = evaluate_baseline(protocol, market(), {**base, "policy": "buy_hold"})
    diag = policy_diagnostics(held)
    assert held.decisions[0]["exposure_before"] == 0
    assert diag["active_intervals"] == 3 and diag["flat_decision_fraction"] == 0
    assert diag["action_counts"]["hold"] == 2
    assert diag["reward_sum"] == pytest.approx(
        diag["gross_return_sum"] - diag["cost_fraction_sum"] - diag["risk_penalty_sum"]
    )
    assert diag["drawdown"]["max_drawdown"] > 0
