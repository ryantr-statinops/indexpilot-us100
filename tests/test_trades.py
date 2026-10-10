from datetime import date

import pytest

from indexpilot_us100.portfolio import Account, TargetExposure, rebalance
from indexpilot_us100.portfolio.trades import TradeTracker
from indexpilot_us100.portfolio.transition import liquidate


def test_scale_and_reverse_reconcile():
    tracker = TradeTracker()
    account = Account(100000)
    day = date(2020, 1, 1)
    for price, next_price, target in [(100, 110, 0.5), (110, 105, 0.25), (105, 100, -0.5)]:
        account, execution = rebalance(account, price, TargetExposure(target), 0.001)
        tracker.execute(day, execution)
        tracker.accrue(account.holdings * (next_price - price))
    result = liquidate(account, 100, 0.001)
    tracker.execute(day, result.execution)
    assert len(tracker.closed) == 2
    assert tracker.active is None
    assert sum(trade["net_pnl"] for trade in tracker.closed) == pytest.approx(
        result.account.cash - 100000
    )
    assert tracker.closed[0]["direction"] == 1
    assert tracker.closed[1]["direction"] == -1
