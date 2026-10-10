"""Readable tabular Q-learning, epsilon-greedy actions and safe persistence."""

import json
from pathlib import Path

import numpy as np

from indexpilot_us100.portfolio import TargetExposure

from .config import LearningConfig
from .state import ACTIONS, BIN_EDGES, FEATURE_NAMES, STATE_COUNT, encode_state


class QLearningAgent:
    def __init__(self, config: LearningConfig = LearningConfig(), name="q_learning"):
        self.config, self.name = config, name
        self.q = np.zeros((STATE_COUNT, len(ACTIONS)), dtype=np.float64)
        self.visits = np.zeros(self.q.shape, dtype=np.int64)
        self.epsilon = 0.0
        self.reset(42)

    def reset(self, seed: int):
        self.rng = np.random.default_rng(seed)

    def choose(self, state: int) -> int:
        self._state(state)
        if self.rng.random() < self.epsilon:
            return int(self.rng.integers(len(ACTIONS)))
        values = self.q[state]
        # Flat, small long, small short, full long, full short.
        return next(index for index in (2, 3, 1, 4, 0) if values[index] == np.max(values))

    def decide(self, observation):
        return TargetExposure(ACTIONS[self.choose(encode_state(observation))])

    @staticmethod
    def _state(state):
        if type(state) is not int or not 0 <= state < STATE_COUNT:
            raise ValueError("Invalid state index")

    def update(
        self, state: int, action: int, reward: float, next_state: int | None, terminated: bool
    ):
        self._state(state)
        if type(action) is not int or not 0 <= action < len(ACTIONS) or not np.isfinite(reward):
            raise ValueError("Invalid action/reward")
        if type(terminated) is not bool:
            raise ValueError("terminated must be bool")
        if not terminated:
            self._state(next_state)
        target = (
            reward if terminated else reward + self.config.gamma * float(np.max(self.q[next_state]))
        )
        error = target - self.q[state, action]
        value = self.q[state, action] + self.config.alpha * error
        if not np.isfinite(value):
            raise ValueError("Q update overflow")
        self.q[state, action] = value
        self.visits[state, action] += 1
        return float(error)

    def save(self, path: str | Path):
        metadata = json.dumps(
            dict(schema_version=1, actions=ACTIONS, features=FEATURE_NAMES, bin_edges=BIN_EDGES)
        )
        np.savez_compressed(path, q=self.q, visits=self.visits, metadata=np.array(metadata))

    @classmethod
    def load(cls, path: str | Path, config: LearningConfig = LearningConfig(), name="q_learning"):
        agent = cls(config, name)
        with np.load(path, allow_pickle=False) as archive:
            metadata = json.loads(str(archive["metadata"]))
            expected = dict(
                schema_version=1,
                actions=list(ACTIONS),
                features=list(FEATURE_NAMES),
                bin_edges=[list(edges) for edges in BIN_EDGES],
            )
            if metadata != expected:
                raise ValueError("Q table has incompatible state/action definitions")
            q, visits = archive["q"], archive["visits"]
            if (
                q.shape != agent.q.shape
                or q.dtype != np.float64
                or not np.all(np.isfinite(q))
                or visits.shape != q.shape
                or visits.dtype != np.int64
                or np.any(visits < 0)
            ):
                raise ValueError("Invalid Q table/visit arrays")
            agent.q, agent.visits = q.copy(), visits.copy()
        return agent
