"""Causal deterministic runner with an event ledger and interval returns."""
from dataclasses import dataclass, field
from datetime import date
from typing import Protocol
from .account import Account, TargetExposure, HoldPosition
from .config import SimulationConfig
from .market import MarketData, MarketFeatures, decision_indices, market_features
from .records import account_event, order_record
from .trades import TradeTracker
from .transition import advance_interval, interval_reward, liquidate


@dataclass(frozen=True)
class Observation:
    index: int
    date: date
    features: MarketFeatures
    cash: float
    holdings: float
    equity: float
    exposure: float
    drawdown: float


class Policy(Protocol):
    name: str

    def reset(self, seed: int) -> None: ...

    def decide(self, observation: Observation) -> TargetExposure | HoldPosition: ...


@dataclass
class SimulationResult:
    baseline: str
    config: SimulationConfig
    status: str
    equity: list[dict]
    ledger: list[dict]
    orders: list[dict]
    trades: list[dict]
    intervals: list[dict]
    warnings: tuple[str, ...]


def _observation(market: MarketData, index: int, account: Account, equity: float, peak: float, risk_window: int) -> Observation:
    price = float(market.opens[index])
    return Observation(
        index, market.dates[index], market_features(market, index, risk_window),
        account.cash, account.holdings, equity, account.exposure(price), 1 - equity / peak,
    )


@dataclass
class _EpisodeRecorder:
    peak: float
    ledger: list[dict] = field(default_factory=list)
    orders: list[dict] = field(default_factory=list)
    tracker: TradeTracker = field(default_factory=TradeTracker)

    def event(self, account: Account, day: date, kind: str, price: float, fee: float = 0., notional: float = 0.) -> dict:
        record = account_event(len(self.ledger), day, kind, account, float(price), fee, notional)
        self.ledger.append(record)
        self.peak = max(self.peak, record['equity'])
        return record

    def record_order(self, day: date, execution, kind: str) -> None:
        if execution.traded_notional:
            self.orders.append(order_record(len(self.orders), day, execution, kind))
        self.tracker.execute(day, execution)


def _finalize_rejected_rebalance(account: Account, day: date, price: float, cost_rate: float, recorder: _EpisodeRecorder, intervals: list[dict], equity: list[dict], error: ValueError):
    # With extreme short drift, even closing fees can exhaust positive equity.
    final = liquidate(account, price, cost_rate)
    account = final.account
    recorder.record_order(day, final.execution, 'liquidation')
    closed = recorder.event(account, day, 'liquidation', price, final.execution.fee, final.execution.traded_notional)
    if not intervals:
        raise ValueError('Unable to execute initial target') from error
    previous = intervals[-1]
    previous['fees'] += final.execution.fee
    previous['cost_fraction'] += final.execution.fee / previous['start_equity']
    previous['reward'] -= final.execution.fee / previous['start_equity']
    previous['end_equity'] = closed['equity']
    previous['net_return'] = closed['equity'] / previous['start_equity'] - 1
    equity[-1] = {**closed, 'net_return': previous['net_return'], 'reward': previous['reward']}
    return final


def run_episode(market: MarketData, policy: Policy, config: SimulationConfig = SimulationConfig()) -> SimulationResult:
    indices = decision_indices(market, config.risk_window)
    policy.reset(config.seed)
    account = Account(config.initial_equity)
    recorder = _EpisodeRecorder(config.initial_equity)
    ledger = recorder.ledger
    orders = recorder.orders
    tracker = recorder.tracker
    equity, intervals = [], []
    status = 'completed'

    first = indices.start
    initial = recorder.event(account, market.dates[first], 'initial', market.opens[first])
    equity.append({**initial, 'net_return': 0., 'reward': 0.})

    for index in indices:
        day, next_day = market.dates[index:index+2]
        price, next_price = map(float, market.opens[index:index+2])
        before = account.equity(price)
        observation = _observation(market, index, account, before, recorder.peak, config.risk_window)
        action = policy.decide(observation)
        try:
            interval = advance_interval(account, price, next_price, action, config.cost_rate)
        except ValueError as error:
            if str(error) != 'Insufficient equity for target after fees':
                raise
            final = _finalize_rejected_rebalance(account, day, price, config.cost_rate, recorder, intervals, equity, error)
            account, status = final.account, final.status
            break
        account = interval.account
        recorder.record_order(day, interval.execution, 'rebalance')
        recorder.event(account, day, 'execution' if interval.execution.traded_notional else 'hold', price, interval.execution.fee, interval.execution.traded_notional)
        tracker.accrue(interval.gross_pnl)
        recorder.event(account, next_day, 'mark', next_price)
        closing_fee = 0.
        if index == indices.stop - 1 or account.equity(next_price) <= 0:
            final = liquidate(account, next_price, config.cost_rate)
            account, status = final.account, final.status
            closing_fee = final.execution.fee
            recorder.record_order(next_day, final.execution, 'liquidation')
            recorder.event(account, next_day, 'liquidation', next_price, closing_fee, final.execution.traded_notional)
        reward = interval_reward(interval, observation.features.volatility, config.risk_lambda, closing_fee)
        end_equity = account.equity(next_price)
        net_return = end_equity / before - 1
        intervals.append(dict(date=day, end_date=next_day, start_equity=before, end_equity=end_equity, gross_pnl=interval.gross_pnl, gross_return=reward.gross_return, fees=interval.execution.fee + closing_fee, cost_fraction=reward.cost_fraction, risk=reward.risk, reward=reward.value, net_return=net_return))
        equity.append({**ledger[-1], 'net_return': net_return, 'reward': reward.value})
        if status == 'insolvent':
            break
    return SimulationResult(policy.name, config, status, equity, ledger, orders, tracker.closed, intervals, market.warnings)
