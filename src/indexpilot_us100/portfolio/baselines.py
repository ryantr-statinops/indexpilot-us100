"""Transparent reference policies using the shared execution engine."""

from .account import HoldPosition, TargetExposure
from .simulator import Observation


class CashPolicy:
    name = "cash"

    def reset(self, seed: int):
        pass

    def decide(self, observation: Observation):
        return TargetExposure(0.0)


class BuyHoldPolicy:
    name = "buy_hold"

    def reset(self, seed: int):
        self.entered = False

    def decide(self, observation: Observation):
        if not self.entered:
            self.entered = True
            return TargetExposure(1.0)
        return HoldPosition()


def baseline_policies():
    return [
        CashPolicy(),
        BuyHoldPolicy(),
        FixedExposurePolicy(0.5, "fixed_long_50"),
        FixedExposurePolicy(-0.5, "fixed_short_50"),
        SMAPolicy(),
        RandomPolicy(),
    ]


class FixedExposurePolicy:
    def __init__(self, value: float, name: str):
        self.action = TargetExposure(value)
        self.name = name

    def reset(self, seed: int):
        pass

    def decide(self, observation: Observation):
        return self.action


class SMAPolicy:
    name = "sma20_long_flat"

    def reset(self, seed: int):
        pass

    def decide(self, observation: Observation):
        return TargetExposure(
            1.0 if observation.features.prior_close > observation.features.sma20 else 0.0
        )


class RandomPolicy:
    name = "random_discrete"

    def reset(self, seed: int):
        import numpy as np

        self.rng = np.random.default_rng(seed)

    def decide(self, observation: Observation):
        return TargetExposure(float(self.rng.choice([-1.0, -0.5, 0.0, 0.5, 1.0])))
