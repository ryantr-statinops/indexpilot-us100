"""Declared scenario matrix; never rank policies or seeds on test."""

from .types import FrozenProtocol, Scenario
from .runner import EvaluatedRun
from indexpilot_us100.portfolio.market import MarketData
from .runner import baseline_scenarios, evaluate_baseline, evaluate_frozen_policy


def scenario_id(scenario: Scenario) -> str:
    policy = (
        f"q_lambda_{scenario['risk_lambda']:g}" if scenario["kind"] == "rl" else scenario["policy"]
    )
    return f"{scenario['kind']}_{policy}_seed_{scenario['seed']}_cost_{scenario['cost_bps']:g}".replace(
        ".", "_"
    )


def scenarios(protocol: FrozenProtocol) -> list[Scenario]:
    config = protocol["evaluation_config"]
    rows = []
    for cost in config["costs_bps"]:
        for seed in config["seeds"]:
            for risk_lambda in (config["reference_lambda"], config["primary_lambda"]):
                rows.append(
                    dict(
                        kind="rl",
                        policy=f"q_lambda_{risk_lambda:g}",
                        seed=seed,
                        risk_lambda=risk_lambda,
                        cost_bps=cost,
                    )
                )
        rows.extend(baseline_scenarios(protocol, cost))
    return [{**row, "scenario_id": scenario_id(row)} for row in rows]


def evaluate_scenario(
    root, protocol: FrozenProtocol, segment: MarketData, scenario: Scenario
) -> EvaluatedRun:
    if scenario["kind"] == "rl":
        return evaluate_frozen_policy(root, protocol, segment, scenario)
    if scenario["kind"] in ("random", "deterministic"):
        return evaluate_baseline(protocol, segment, scenario)
    raise ValueError("Unknown scenario kind")
