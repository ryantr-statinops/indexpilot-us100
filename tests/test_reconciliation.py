"""Cross-module invariants independent of network and downloaded data."""
from dataclasses import replace
from datetime import date, timedelta
import sys
import numpy as np
import polars as pl
import pytest
from indexpilot_us100.metrics import compute_metrics
from indexpilot_us100.portfolio.account import Account, HoldPosition, TargetExposure, rebalance
from indexpilot_us100.portfolio.baselines import baseline_policies, BuyHoldPolicy, RandomPolicy, FixedExposurePolicy
from indexpilot_us100.portfolio.config import SimulationConfig
from indexpilot_us100.portfolio.market import MarketData
from indexpilot_us100.portfolio.simulator import run_episode
from test_simulator import market, ConstantPolicy


def synthetic_market(seed=8):
    rng = np.random.default_rng(seed)
    opens = 100 * np.exp(np.cumsum(rng.normal(.001, .025, 140)))
    closes = opens * np.exp(rng.normal(0, .008, 140))
    return MarketData.from_frame(pl.DataFrame({'date': [date(2020, 1, 1) + timedelta(days=i) for i in range(140)], 'adj_open': opens, 'adj_close': closes}))


@pytest.mark.parametrize('cost_bps', [0, 10, 20])
@pytest.mark.parametrize('policy_index', range(6))
def test_episode_invariants(cost_bps, policy_index):
    data = synthetic_market()
    policy = baseline_policies()[policy_index]
    result = run_episode(data, policy, SimulationConfig(cost_bps=cost_bps))
    for event in result.ledger:
        assert event['equity'] == pytest.approx(event['cash'] + event['holdings'] * event['price'])
        assert event['fee'] >= 0
        if event['kind'] == 'execution':
            assert abs(event['exposure']) <= 1 + 1e-10
    assert sum(t['net_pnl'] for t in result.trades) == pytest.approx(result.equity[-1]['equity'] - 100000, abs=1e-7)
    assert sum(row['fees'] for row in result.intervals) == pytest.approx(sum(row['fee'] for row in result.orders))
    assert np.prod([1 + row['net_return'] for row in result.intervals]) == pytest.approx(result.equity[-1]['equity'] / 100000)
    for interval in result.intervals:
        assert interval['reward'] == pytest.approx(interval['net_return'], abs=1e-12)
    assert result.equity[-1]['holdings'] == 0


def test_all_baselines_same_schedule_and_lambda():
    data = synthetic_market()
    boundaries = []
    for policy in baseline_policies():
        reference = run_episode(data, policy)
        penalized = run_episode(data, policy, SimulationConfig(risk_lambda=2))
        assert reference.orders == penalized.orders
        assert reference.ledger == penalized.ledger
        for left, right in zip(reference.intervals, penalized.intervals):
            assert right['reward'] == pytest.approx(left['reward'] - 2 * left['risk'])
        boundaries.append(([row['date'] for row in reference.equity], len(reference.intervals)))
    assert all(value == boundaries[0] for value in boundaries)


def test_future_changes_preserve_prefix():
    data = synthetic_market()
    future = 45
    opens, closes = data.opens.copy(), data.closes.copy()
    opens[future:] *= 3
    closes[future:] *= 4
    changed = MarketData(data.dates, opens, closes)
    for policy in baseline_policies():
        left = run_episode(data, policy)
        right = run_episode(changed, policy)
        old = [row for row in left.intervals if row['end_date'] < data.dates[future]]
        new = [row for row in right.intervals if row['end_date'] < data.dates[future]]
        assert old == new


def test_drifting_short_and_fee_insolvency():
    class ShortHold(BuyHoldPolicy):
        name = 'short_hold'
        def decide(self, observation):
            if not self.entered:
                self.entered = True
                return TargetExposure(-1)
            return HoldPosition()
    held = run_episode(market([100.] * 22 + [150., 150.]), ShortHold())
    assert held.status == 'completed'
    assert held.ledger[2]['exposure'] < -1
    assert len(held.orders) == 2
    failed = run_episode(market([100.] * 22 + [199.9, 200.]), ConstantPolicy(-1))
    assert failed.status == 'insolvent'
    assert len(failed.intervals) == 1
    assert failed.intervals[-1]['reward'] == pytest.approx(failed.intervals[-1]['net_return'])
    assert sum(row['net_pnl'] for row in failed.trades) == pytest.approx(failed.equity[-1]['equity'] - 100000)


def test_return_column_is_not_used():
    from test_market import frame
    data = frame().with_columns(pl.lit(1000.).alias('open_to_open_return'))
    left = run_episode(MarketData.from_frame(data), BuyHoldPolicy())
    right = run_episode(MarketData.from_frame(data.drop('open_to_open_return')), BuyHoldPolicy())
    assert left.intervals == right.intervals


def test_repeat_random_and_optional_charts(monkeypatch):
    monkeypatch.setitem(sys.modules, 'finplot', None)
    data = synthetic_market()
    first = run_episode(data, RandomPolicy())
    assert first.orders == run_episode(data, RandomPolicy()).orders
    assert first.orders != run_episode(data, RandomPolicy(), SimulationConfig(seed=43)).orders
    assert compute_metrics(first).metrics['sharpe'].value is not None


@pytest.mark.parametrize('rate', [0, .001, .002, .1])
def test_randomized_target_equation(rate):
    rng = np.random.default_rng(123)
    for _ in range(100):
        equity = float(rng.uniform(100, 1e6))
        price = float(rng.uniform(1, 1000))
        old, target = rng.uniform(-1, 1, 2)
        account = Account(equity * (1-old), equity * old / price)
        after, order = rebalance(account, price, TargetExposure(float(target)), rate)
        assert after.exposure(price) == pytest.approx(target)
        assert after.equity(price) == pytest.approx(equity - order.fee)
        assert order.fee == pytest.approx(rate * abs(order.delta_units) * price)
