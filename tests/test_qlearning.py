import numpy as np
import pytest

from indexpilot_us100.agents.config import LearningConfig
from indexpilot_us100.agents.qlearning import QLearningAgent


def test_toy_bellman_update_and_terminal():
    agent = QLearningAgent(LearningConfig(alpha=0.5, gamma=0.9))
    agent.q[1, 4] = 2
    agent.update(0, 2, 1, 1, False)
    assert agent.q[0, 2] == pytest.approx(1.4)
    agent.update(0, 2, 1, None, True)
    assert agent.q[0, 2] == pytest.approx(1.2)
    assert agent.visits[0, 2] == 2


def test_tie_exploration_and_save(tmp_path):
    agent = QLearningAgent()
    assert agent.choose(0) == 2
    agent.epsilon = 1
    agent.reset(5)
    left = [agent.choose(0) for _ in range(100)]
    agent.reset(5)
    assert left == [agent.choose(0) for _ in range(100)]
    assert set(left) == set(range(5))
    agent.update(0, 1, 0.1, None, True)
    path = tmp_path / "q.npz"
    agent.save(path)
    loaded = QLearningAgent.load(path)
    np.testing.assert_array_equal(agent.q, loaded.q)
    np.testing.assert_array_equal(agent.visits, loaded.visits)
    with pytest.raises(ValueError):
        agent.update(0, 0, float("nan"), None, True)


def test_terminal_bandit_learns_known_best_action():
    agent = QLearningAgent()
    for _ in range(100):
        for action, reward in enumerate([-1, -0.5, 0, 1, 0.5]):
            agent.update(0, action, reward, 999999, True)
    assert agent.choose(0) == 3
    assert agent.q[0, 3] == pytest.approx(1, abs=0.0001)
