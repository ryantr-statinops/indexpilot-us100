"""Validated, serializable experiment settings."""

import math
import tomllib
from dataclasses import dataclass, fields
from pathlib import Path


@dataclass(frozen=True)
class SimulationConfig:
    initial_equity: float = 100_000.0
    cost_bps: float = 10.0
    risk_lambda: float = 0.0
    risk_window: int = 20
    annualization: int = 252
    risk_free_annual: float = 0.0
    seed: int = 42

    def __post_init__(self):
        for name in ("initial_equity", "cost_bps", "risk_lambda", "risk_free_annual"):
            value = getattr(self, name)
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
            ):
                raise ValueError(f"{name} must be finite numeric")
        if self.initial_equity <= 0:
            raise ValueError("initial_equity must be positive")
        if not 0 <= self.cost_bps < 10_000:
            raise ValueError("cost_bps must be in [0, 10000)")
        if self.risk_lambda < 0 or self.risk_free_annual <= -1:
            raise ValueError("risk_lambda must be nonnegative; risk_free_annual must exceed -1")
        for name, minimum in (("risk_window", 2), ("annualization", 1), ("seed", 0)):
            value = getattr(self, name)
            if type(value) is not int or value < minimum:
                raise ValueError(f"{name} must be an integer >= {minimum}")

    @property
    def cost_rate(self):
        return self.cost_bps / 10_000

    @classmethod
    def from_toml(cls, path: str | Path):
        with Path(path).open("rb") as file:
            values = tomllib.load(file)
        unknown = values.keys() - {field.name for field in fields(cls)}
        if unknown:
            raise ValueError(f"Unknown configuration keys: {sorted(unknown)}")
        return cls(**values)
