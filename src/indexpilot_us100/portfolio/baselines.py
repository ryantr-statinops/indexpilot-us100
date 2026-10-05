"""Transparent reference policies using the shared execution engine."""
from .account import TargetExposure, HoldPosition
from .simulator import Observation


class CashPolicy:
    name = 'cash'

    def reset(self, seed: int):
        pass

    def decide(self, observation: Observation):
        return TargetExposure(0.)


class BuyHoldPolicy:
    name = 'buy_hold'

    def reset(self, seed: int):
        self.entered = False

    def decide(self, observation: Observation):
        if not self.entered:
            self.entered = True
            return TargetExposure(1.)
        return HoldPosition()


def baseline_policies():
    return [CashPolicy(), BuyHoldPolicy()]
