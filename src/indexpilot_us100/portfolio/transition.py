"""One interval of accounting, reusable by baselines and future RL."""
from dataclasses import dataclass
from .account import Account, Execution, TargetExposure, HoldPosition, rebalance, validate_price


@dataclass(frozen=True)
class Interval:
    execution: Execution
    account: Account
    start_equity: float
    end_equity: float
    gross_pnl: float

    @property
    def net_return(self):
        return self.end_equity / self.start_equity - 1


def advance_interval(account: Account, price: float, next_price: float, action: TargetExposure | HoldPosition, cost_rate: float = 0.) -> Interval:
    validate_price(next_price)
    start = account.equity(price)
    after, execution = rebalance(account, price, action, cost_rate)
    pnl = after.holdings * (next_price - price)
    return Interval(execution, after, start, after.equity(next_price), pnl)
