"""Finalized RL trajectories without duplicating portfolio accounting."""

from dataclasses import dataclass, replace

from indexpilot_us100.agents import ACTIONS, encode_state
from indexpilot_us100.portfolio import (
    MarketData,
    Observation,
    SimulationConfig,
    SimulationResult,
    TargetExposure,
    decision_indices,
    market_features,
    run_episode,
)


@dataclass(frozen=True)
class Transition:
    state: int
    action: int
    reward: float
    next_state: int | None
    terminated: bool


@dataclass
class Trajectory:
    result: SimulationResult
    transitions: list[Transition]


class TradingEnvironment:
    def __init__(self, market: MarketData, config: SimulationConfig = SimulationConfig()):
        self.market, self.config = market, config
        decision_indices(market, config.risk_window)

    def reset(self, seed: int | None = None) -> Observation:
        if seed is not None:
            self.config = replace(self.config, seed=seed)
        index = decision_indices(self.market, self.config.risk_window).start
        return Observation(
            index,
            self.market.dates[index],
            market_features(self.market, index, self.config.risk_window),
            self.config.initial_equity,
            0.0,
            self.config.initial_equity,
            0.0,
            0.0,
        )

    def rollout(self, policy) -> Trajectory:
        states, actions = [], []

        class Recorder:
            name = policy.name

            def reset(self, seed):
                policy.reset(seed)

            def decide(self, observation):
                action = policy.decide(observation)
                if not isinstance(action, TargetExposure) or action.value not in ACTIONS:
                    raise ValueError("RL environment requires one of the five target actions")
                states.append(encode_state(observation))
                actions.append(ACTIONS.index(action.value))
                return action

        result = run_episode(self.market, Recorder(), self.config)
        count = len(result.intervals)
        # The simulator may reject a fee-insolvent final rebalance and revise the
        # preceding interval. Only finalized financial intervals become transitions.
        transitions = [
            Transition(
                states[i],
                actions[i],
                row["reward"],
                None if i == count - 1 else states[i + 1],
                i == count - 1,
            )
            for i, row in enumerate(result.intervals)
        ]
        return Trajectory(result, transitions)
