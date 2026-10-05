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
