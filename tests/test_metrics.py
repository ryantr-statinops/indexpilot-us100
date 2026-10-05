import numpy as np
import pytest
from indexpilot_us100.metrics import drawdown_curve, compute_metrics
from indexpilot_us100.portfolio.baselines import CashPolicy, BuyHoldPolicy
from indexpilot_us100.portfolio.simulator import run_episode
from test_simulator import market


def test_hand_drawdown():
    assert drawdown_curve([100, 120, 90, 110]).tolist() == pytest.approx([0, 0, .25, 1 - 110/120])
    assert drawdown_curve([100, -10])[-1] == 1.1


def test_initial_fees_in_drawdown():
    result = run_episode(market(), BuyHoldPolicy())
    report = compute_metrics(result)
    assert report.metrics['max_drawdown'].value >= result.orders[0]['fee'] / 100000
    assert report.summary['trade_count'] == 1
    cash = compute_metrics(run_episode(market(), CashPolicy()))
    assert cash.summary['net_return'] == cash.summary['total_fees'] == cash.metrics['max_drawdown'].value == 0
