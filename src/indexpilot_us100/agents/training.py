"""Chronological training and validation-only selection."""

from bisect import bisect_left, bisect_right
from dataclasses import dataclass, replace
from datetime import date

import numpy as np

from indexpilot_us100.environment.trading import TradingEnvironment, Trajectory
from indexpilot_us100.metrics import compute_metrics
from indexpilot_us100.portfolio.baselines import baseline_policies
from indexpilot_us100.portfolio.config import SimulationConfig
from indexpilot_us100.portfolio.market import MarketData, decision_indices

from .config import LearningConfig
from .qlearning import QLearningAgent


@dataclass
class Experiment:
    risk_lambda: float
    agent: QLearningAgent
    training_log: list[dict]
    greedy_train: Trajectory
    validation: Trajectory
    baselines: list


def chronological_segments(
    market: MarketData, learning: LearningConfig, simulation: SimulationConfig
):
    dates = market.dates
    train_stop = bisect_right(dates, date.fromisoformat(learning.train_end))
    validation_first = bisect_left(dates, date.fromisoformat(learning.validation_start))
    validation_stop = bisect_right(dates, date.fromisoformat(learning.validation_end))
    warmup = max(20, simulation.risk_window) + 1
    if validation_first < warmup or validation_stop <= validation_first + 1:
        raise ValueError("Validation needs prior warm-up and at least two in-range opens")

    def segment(start, stop):
        result = MarketData(
            dates[start:stop], market.opens[start:stop], market.closes[start:stop], market.warnings
        )
        decision_indices(result, simulation.risk_window)
        return result

    return segment(0, train_stop), segment(validation_first - warmup, validation_stop)


def train_agent(
    market: MarketData, simulation: SimulationConfig, learning: LearningConfig, progress=None
):
    agent = QLearningAgent(learning, name=f"q_lambda_{simulation.risk_lambda:g}".replace(".", "_"))
    env = TradingEnvironment(market, simulation)
    logs = []
    for episode in range(learning.episodes):
        seed = simulation.seed + episode
        env.reset(seed)
        agent.epsilon = learning.epsilon(episode)
        trajectory = env.rollout(agent)
        errors = [
            agent.update(t.state, t.action, t.reward, t.next_state, t.terminated)
            for t in trajectory.transitions
        ]
        result = trajectory.result
        counts = np.bincount([t.action for t in trajectory.transitions], minlength=5)
        row = dict(
            episode=episode + 1,
            seed=seed,
            epsilon=agent.epsilon,
            risk_lambda=simulation.risk_lambda,
            training_reward=sum(t.reward for t in trajectory.transitions),
            net_return=result.equity[-1]["equity"] / simulation.initial_equity - 1,
            final_equity=result.equity[-1]["equity"],
            fees=sum(order["fee"] for order in result.orders),
            transition_count=len(errors),
            visited_states=int(np.count_nonzero(agent.visits.sum(axis=1))),
            mean_absolute_td_error=float(np.mean(np.abs(errors))),
            status=result.status,
            **{f"action_{i}_count": int(value) for i, value in enumerate(counts)},
        )
        logs.append(row)
        if progress and (
            episode == 0 or (episode + 1) % 10 == 0 or episode + 1 == learning.episodes
        ):
            progress(
                f"lambda={simulation.risk_lambda:g} episode={episode + 1}/{learning.episodes} epsilon={agent.epsilon:.3f} reward={row['training_reward']:.4f}"
            )
    agent.epsilon = 0.0
    return agent, logs


def run_experiments(market, simulation, learning, progress=None):
    train, validation = chronological_segments(market, learning, simulation)
    experiments = []
    for risk_lambda in learning.lambdas:
        config = replace(simulation, risk_lambda=risk_lambda)
        agent, logs = train_agent(train, config, learning, progress)
        greedy_train = TradingEnvironment(train, config).rollout(agent)
        greedy_validation = TradingEnvironment(validation, config).rollout(agent)
        from indexpilot_us100.portfolio.simulator import run_episode

        baselines = [run_episode(validation, policy, config) for policy in baseline_policies()]
        experiments.append(
            Experiment(risk_lambda, agent, logs, greedy_train, greedy_validation, baselines)
        )
    scored = [
        (index, compute_metrics(experiment.validation.result).metrics["sharpe"])
        for index, experiment in enumerate(experiments)
    ]
    eligible = [
        (index, metric.value)
        for index, metric in scored
        if metric.status == "finite" and experiments[index].validation.result.status == "completed"
    ]
    selected = max(eligible, key=lambda item: (item[1], -item[0]))[0] if eligible else 0
    selection = dict(
        selected_lambda=experiments[selected].risk_lambda,
        selected_index=selected,
        criterion="greedy_validation_sharpe",
        status="selected" if eligible else "undefined_fallback_lambda_zero",
        test_evaluated=False,
    )
    return experiments, selection
