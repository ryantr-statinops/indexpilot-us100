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


@dataclass(frozen=True)
class Reward:
    gross_return: float
    cost_fraction: float
    risk: float
    value: float


def interval_reward(interval: Interval, volatility: float, risk_lambda: float = 0., closing_fee: float = 0.) -> Reward:
    import math
    if not all(math.isfinite(value) and value >= 0 for value in (volatility, risk_lambda, closing_fee)):
        raise ValueError('Volatility, lambda and closing fee must be finite and nonnegative')
    gross = interval.gross_pnl / interval.start_equity
    cost = (interval.execution.fee + closing_fee) / interval.start_equity
    risk = abs(interval.account.holdings * interval.execution.price / interval.start_equity) * volatility
    return Reward(gross, cost, risk, gross - risk_lambda * risk - cost)


@dataclass(frozen=True)
class Finalization:
    account: Account
    execution: Execution
    status: str


def liquidate(account: Account, price: float, cost_rate: float) -> Finalization:
    """Close units even when equity is nonpositive; retain resulting debt."""
    import math
    validate_price(price)
    if not math.isfinite(cost_rate) or not 0 <= cost_rate < 1:
        raise ValueError('Cost rate must be in [0, 1)')
    notional = account.holdings * price
    fee = abs(notional) * cost_rate
    after = Account(account.cash + notional - fee, 0.)
    execution = Execution(account, after, price, 0., abs(notional), fee)
    return Finalization(after, execution, 'insolvent' if after.equity(price) <= 0 else 'completed')
