from dataclasses import replace

from final_helpers import source_fixture

from indexpilot_us100.agents.qlearning import QLearningAgent
from indexpilot_us100.evaluation.final.protocol import prepare_protocol
from indexpilot_us100.evaluation.final.runner import evaluate_frozen_policy
from indexpilot_us100.evaluation.final.windows import build_test_segment
from indexpilot_us100.portfolio.config import SimulationConfig
from indexpilot_us100.portfolio.market import load_market_data


def test_immutable_greedy_eval(tmp_path, monkeypatch):
    data, source, config = source_fixture(tmp_path)
    config = replace(config, seeds=(42,))
    root = tmp_path / "frozen"
    protocol = prepare_protocol(data, source, config, root)
    segment = build_test_segment(load_market_data(data), config, SimulationConfig())

    def forbidden(*args, **kwargs):
        raise AssertionError("Evaluation called update")

    monkeypatch.setattr(QLearningAgent, "update", forbidden)
    scenario = dict(kind="rl", seed=42, risk_lambda=2.0, cost_bps=10.0)
    result = evaluate_frozen_policy(root, protocol, segment, scenario)
    assert not result.agent.q.flags.writeable
    assert not result.agent.visits.flags.writeable
    assert result.result.equity[0]["cash"] == 100000
    assert result.result.equity[0]["date"].isoformat() == "2020-05-01"


def test_baselines_are_not_duplicated():
    from dataclasses import asdict

    from test_simulator import market

    from indexpilot_us100.evaluation.final.config import EvaluationConfig
    from indexpilot_us100.evaluation.final.runner import baseline_scenarios, evaluate_baseline

    protocol = {
        "evaluation_config": asdict(EvaluationConfig()),
        "simulation_config": asdict(SimulationConfig()),
    }
    scenarios = baseline_scenarios(protocol, 10)
    assert len(scenarios) == 10
    assert sum(row["kind"] == "deterministic" for row in scenarios) == 5
    assert sum(row["kind"] == "random" for row in scenarios) == 5
    results = [evaluate_baseline(protocol, market(), row).result for row in scenarios]
    assert all(result.equity[0]["date"] == results[0].equity[0]["date"] for result in results)
