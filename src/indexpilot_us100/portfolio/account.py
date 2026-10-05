"""Synthetic fractional holdings and cash accounting."""
from dataclasses import dataclass
import math


def validate_price(price: float):
    if not math.isfinite(price) or price <= 0:
        raise ValueError('Price must be finite and positive')


@dataclass(frozen=True)
class Account:
    cash: float
    holdings: float = 0.0

    def __post_init__(self):
        if not math.isfinite(self.cash) or not math.isfinite(self.holdings):
            raise ValueError('Cash and holdings must be finite')

    def equity(self, price: float) -> float:
        validate_price(price)
        value = self.cash + self.holdings * price
        if not math.isfinite(value):
            raise ValueError('Account valuation overflow')
        return value

    def exposure(self, price: float) -> float | None:
        equity = self.equity(price)
        return self.holdings * price / equity if equity > 0 else None


@dataclass(frozen=True)
class TargetExposure:
    value: float

    def __post_init__(self):
        if not math.isfinite(self.value) or not -1 <= self.value <= 1:
            raise ValueError('Target exposure must be finite and in [-1, 1]')


@dataclass(frozen=True)
class HoldPosition:
    """Keep units unchanged, even when their weight drifts."""


@dataclass(frozen=True)
class Execution:
    before: Account
    after: Account
    price: float
    target: float | None
    traded_notional: float
    fee: float = 0.0

    @property
    def delta_units(self):
        return self.after.holdings - self.before.holdings


def rebalance(account: Account, price: float, target: TargetExposure | HoldPosition, cost_rate: float = 0.0) -> tuple[Account, Execution]:
    validate_price(price)
    if cost_rate != 0:
        raise ValueError('Costs are not supported yet')
    equity = account.equity(price)
    if equity <= 0:
        raise ValueError('Cannot rebalance a non-positive account')
    if isinstance(target, HoldPosition):
        return account, Execution(account, account, price, None, 0.)
    if not isinstance(target, TargetExposure):
        raise TypeError('Expected TargetExposure or HoldPosition')
    notional = target.value * equity
    delta = notional - account.holdings * price
    after = Account(account.cash - delta, notional / price)
    return after, Execution(account, after, price, target.value, abs(delta))
