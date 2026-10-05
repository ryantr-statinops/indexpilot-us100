"""Predeclared learning settings and chronological validation boundaries."""
from dataclasses import dataclass, fields
from datetime import date
import math
from pathlib import Path
import tomllib
from indexpilot_us100.portfolio.config import SimulationConfig


@dataclass(frozen=True)
class LearningConfig:
    episodes: int = 100
    alpha: float = .1
    gamma: float = .99
    epsilon_start: float = 1.
    epsilon_decay: float = .97
    epsilon_min: float = .05
    lambdas: tuple[float, ...] = (0., .5, 1., 2.)
    train_end: str = '2020-12-31'
    validation_start: str = '2021-01-01'
    validation_end: str = '2022-12-31'
    test_start: str = '2023-01-01'

    def __post_init__(self):
        if type(self.episodes) is not int or self.episodes < 1:
            raise ValueError('episodes must be a positive integer')
        for name in ('alpha', 'gamma', 'epsilon_start', 'epsilon_decay', 'epsilon_min'):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 1:
                raise ValueError(f'{name} must be finite in [0,1]')
        if self.alpha == 0 or self.epsilon_decay == 0 or self.epsilon_min > self.epsilon_start:
            raise ValueError('alpha/epsilon_decay must be positive; epsilon_min <= epsilon_start')
        if not self.lambdas or len(set(self.lambdas)) != len(self.lambdas) or self.lambdas[0] != 0 or any(isinstance(value, bool) or not isinstance(value, (int,float)) or not math.isfinite(value) or value < 0 for value in self.lambdas):
            raise ValueError('lambdas must be unique nonnegative finite numbers starting with 0')
        try:
            boundaries = [date.fromisoformat(getattr(self, name)) for name in ('train_end', 'validation_start', 'validation_end', 'test_start')]
        except (ValueError, TypeError) as error:
            raise ValueError('Split boundaries must be ISO dates') from error
        if not boundaries[0] < boundaries[1] <= boundaries[2] < boundaries[3]:
            raise ValueError('Training, validation and reserved test dates must be chronological')

    def epsilon(self, episode: int):
        return max(self.epsilon_min, self.epsilon_start * self.epsilon_decay ** episode)


def load_learning_config(path: str | Path):
    with Path(path).open('rb') as file:
        values = tomllib.load(file)
    if values.keys() - {'simulation', 'learning'}:
        raise ValueError('Only [simulation] and [learning] sections are supported')
    learning = dict(values.get('learning', {}))
    unknown = learning.keys() - {field.name for field in fields(LearningConfig)}
    if unknown:
        raise ValueError(f'Unknown learning keys: {sorted(unknown)}')
    if 'lambdas' in learning:
        learning['lambdas'] = tuple(learning['lambdas'])
    simulation = SimulationConfig(**values.get('simulation', {}))
    if simulation.risk_lambda != 0:
        raise ValueError('Base simulation risk_lambda must be 0; use learning.lambdas for the sweep')
    return simulation, LearningConfig(**learning)
