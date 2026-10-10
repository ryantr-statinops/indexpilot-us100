"""Declared test boundaries, seeds and execution sensitivity."""

import math
import tomllib
from dataclasses import dataclass, fields
from datetime import date
from pathlib import Path


@dataclass(frozen=True)
class EvaluationConfig:
    source_run: str = "outputs/stage-3/aapl-default"
    test_start: str = "2023-01-01"
    test_end: str = "2026-10-02"
    primary_seed: int = 42
    seeds: tuple[int, ...] = (42, 7, 21, 84, 123)
    primary_lambda: float = 2.0
    reference_lambda: float = 0.0
    primary_cost_bps: float = 10.0
    costs_bps: tuple[float, ...] = (0.0, 10.0, 20.0)

    instrument_label: str | None = None

    def __post_init__(self) -> None:
        if self.instrument_label is not None and (
            not isinstance(self.instrument_label, str)
            or not self.instrument_label.strip()
            or any(character in self.instrument_label for character in "\r\n")
        ):
            raise ValueError("instrument_label must be a nonblank single-line string or None")
        if not isinstance(self.source_run, str) or not self.source_run:
            raise ValueError("source_run must be a nonempty path")
        try:
            start, end = date.fromisoformat(self.test_start), date.fromisoformat(self.test_end)
        except (TypeError, ValueError) as error:
            raise ValueError("Test dates must be ISO dates") from error
        if end <= start:
            raise ValueError("Test end must follow test start")
        if (
            type(self.primary_seed) is not int
            or not self.seeds
            or any(type(seed) is not int or seed < 0 for seed in self.seeds)
            or len(set(self.seeds)) != len(self.seeds)
            or self.primary_seed not in self.seeds
        ):
            raise ValueError("Seeds must be unique nonnegative integers including primary seed")
        for values in (
            self.costs_bps,
            (self.primary_cost_bps, self.primary_lambda, self.reference_lambda),
        ):
            if any(
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                or value < 0
                for value in values
            ):
                raise ValueError("Costs/lambdas must be finite nonnegative numbers")
        if (
            not self.costs_bps
            or len(set(self.costs_bps)) != len(self.costs_bps)
            or max(self.costs_bps) >= 10000
            or self.primary_cost_bps not in self.costs_bps
        ):
            raise ValueError("Costs must be unique in [0,10000) and include primary cost")
        if self.primary_lambda == self.reference_lambda:
            raise ValueError("Primary and reference lambda must differ")

    @classmethod
    def from_toml(cls, path: str | Path) -> "EvaluationConfig":
        with Path(path).open("rb") as file:
            values = tomllib.load(file)
        unknown = values.keys() - {field.name for field in fields(cls)}
        if unknown:
            raise ValueError(f"Unknown evaluation keys: {sorted(unknown)}")
        for name in ("seeds", "costs_bps"):
            if name in values:
                values[name] = tuple(values[name])
        return cls(**values)

    @property
    def scenario_count(self) -> int:
        return len(self.costs_bps) * (len(self.seeds) * 3 + 5)
