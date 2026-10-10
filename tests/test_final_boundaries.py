"""Boundary and conservation checks before any real reserved test is opened."""

import json
from dataclasses import asdict, replace
from datetime import date, timedelta

import numpy as np
import pytest
from final_helpers import source_fixture
from test_reconciliation import synthetic_market
from test_simulator import market

from indexpilot_us100.evaluation.final.config import EvaluationConfig
from indexpilot_us100.evaluation.final.diagnostics import drawdown_events, policy_diagnostics
from indexpilot_us100.evaluation.final.preparation import prepare_models
from indexpilot_us100.evaluation.final.protocol import prepare_protocol, validate_protocol
from indexpilot_us100.evaluation.final.runner import baseline_scenarios, evaluate_baseline
from indexpilot_us100.evaluation.final.source import validate_source
from indexpilot_us100.evaluation.final.windows import build_test_segment
from indexpilot_us100.portfolio.baselines import baseline_policies
from indexpilot_us100.portfolio.config import SimulationConfig
from indexpilot_us100.portfolio.market import MarketData, load_market_data
from indexpilot_us100.portfolio.simulator import run_episode


def test_prepare_q_does_not_use_changed_validation_or_test(tmp_path):
    data, source, config = source_fixture(tmp_path)
    validated = validate_source(data, source, config)
    original = load_market_data(data)
    values = original.opens.copy()
    closes = original.closes.copy()
    for i, day in enumerate(original.dates):
        if day > date.fromisoformat(validated.learning.train_end):
            values[i] *= 3
            closes[i] *= 2
    changed = MarketData(original.dates, values, closes, original.warnings)
    config = replace(config, seeds=(42, 7))
    left = prepare_models(original, validated, config, tmp_path / "left")
    right = prepare_models(changed, validated, config, tmp_path / "right")
    for a, b in zip(left, right):
        with (
            np.load(tmp_path / "left" / a["model"]) as one,
            np.load(tmp_path / "right" / b["model"]) as two,
        ):
            np.testing.assert_array_equal(one["q"], two["q"])
            np.testing.assert_array_equal(one["visits"], two["visits"])


@pytest.mark.parametrize("name", [policy.name for policy in baseline_policies()])
def test_stage2_parity_and_accounting(name):
    simulation = SimulationConfig(risk_lambda=2.0)
    protocol = dict(
        evaluation_config=asdict(EvaluationConfig()), simulation_config=asdict(simulation)
    )
    scenario = next(
        row
        for row in baseline_scenarios(protocol, 10.0)
        if row["policy"] == name and row["seed"] == 42
    )
    evaluated = evaluate_baseline(protocol, synthetic_market(), scenario)
    direct = run_episode(
        synthetic_market(), next(p for p in baseline_policies() if p.name == name), simulation
    )
    assert evaluated.result.ledger == direct.ledger
    assert evaluated.result.intervals == direct.intervals
    result = evaluated.result
    assert sum(row["net_pnl"] for row in result.trades) == pytest.approx(
        result.equity[-1]["equity"] - 100000, abs=1e-7
    )
    for row in result.ledger:
        assert row["equity"] == pytest.approx(row["cash"] + row["holdings"] * row["price"])
    diag = policy_diagnostics(evaluated)
    assert diag["gross_return_sum"] - diag["cost_fraction_sum"] - diag[
        "risk_penalty_sum"
    ] == pytest.approx(diag["reward_sum"])


def test_future_changes_preserve_finished_prefix():
    original = synthetic_market()
    values = original.opens.copy()
    closes = original.closes.copy()
    values[90:] *= 2
    closes[90:] *= 2
    changed = MarketData(original.dates, values, closes, original.warnings)
    protocol = dict(
        evaluation_config=asdict(EvaluationConfig()), simulation_config=asdict(SimulationConfig())
    )
    for scenario in baseline_scenarios(protocol, 10.0):
        a = evaluate_baseline(protocol, original, scenario)
        b = evaluate_baseline(protocol, changed, scenario)
        assert a.decisions[:60] == b.decisions[:60]
        assert a.result.intervals[:60] == b.result.intervals[:60]


def test_nontrading_boundary_keeps_warmup():
    source = synthetic_market()
    indices = [i for i, day in enumerate(source.dates) if day.weekday() < 5]
    weekdays = MarketData(
        tuple(source.dates[i] for i in indices),
        source.opens[indices],
        source.closes[indices],
        source.warnings,
    )
    config = EvaluationConfig(test_start="2020-05-02", test_end="2020-05-19")
    segment = build_test_segment(weekdays, config, SimulationConfig())
    assert segment.dates[21] == date(2020, 5, 4)


def test_insolvency_activity_coverage_and_drawdown():
    protocol = dict(
        evaluation_config=asdict(EvaluationConfig()),
        simulation_config=asdict(SimulationConfig(risk_lambda=2.0)),
    )
    scenario = next(
        row for row in baseline_scenarios(protocol, 10.0) if row["policy"] == "fixed_short_50"
    )
    run = evaluate_baseline(protocol, market([100.0] * 22 + [500.0, 600.0, 700.0]), scenario)
    assert run.result.status == "insolvent" and len(run.result.intervals) == 1
    assert run.result.equity[-1]["holdings"] == 0 and run.result.equity[-1]["equity"] < 0
    diag = policy_diagnostics(run)
    assert "insolvent" in diag["flags"] and diag["active_intervals"] == 1
    # Time between rising peaks is not underwater.
    ledger = [
        dict(sequence=i, date=date(2020, 1, 1) + timedelta(days=d), equity=v)
        for i, (d, v) in enumerate([(0, 100), (100, 110), (101, 90), (102, 120)])
    ]
    assert drawdown_events(ledger)["max_underwater_calendar_days"] == 2


@pytest.mark.parametrize("kind", ["data", "config", "code", "state", "log"])
def test_locked_input_changes_rejected(tmp_path, monkeypatch, kind):
    data, source, config = source_fixture(tmp_path)
    root = tmp_path / "final"
    protocol = prepare_protocol(data, source, replace(config, seeds=(42,)), root)
    if kind == "data":
        data.write_bytes(b"changed")
    elif kind == "code":
        monkeypatch.setattr(
            "indexpilot_us100.evaluation.final.protocol.code_fingerprints", lambda: {}
        )
    elif kind == "log":
        (root / protocol["models"][0]["training_log"]).write_text("changed")
    else:
        if kind == "config":
            protocol["evaluation_config"]["primary_lambda"] = 1.0
        else:
            protocol["state_definition"]["actions"] = [0.0]
        (root / "protocol.json").write_text(json.dumps(protocol))
    with pytest.raises(ValueError):
        validate_protocol(root)
