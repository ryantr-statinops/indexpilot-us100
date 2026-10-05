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


def test_sharpe_and_calendar_cagr():
    from indexpilot_us100.metrics import sharpe_ratio, compound_growth
    returns = [.01, -.02, .03]
    assert sharpe_ratio(returns).value == pytest.approx(np.mean(returns) / np.std(returns, ddof=1) * np.sqrt(252))
    assert compound_growth(100, 121, 730.5).value == pytest.approx(.1)
    assert compound_growth(100, -1, 365).status == 'undefined'
    assert sharpe_ratio([0, 0]).status == 'undefined'
    assert sharpe_ratio([.01]).status == 'undefined'
    assert sharpe_ratio([.01, .02], risk_free_annual=.05).value < sharpe_ratio([.01, .02]).value


def test_insolvent_metrics():
    from test_simulator import ConstantPolicy
    result = run_episode(market([100.] * 22 + [300., 400.]), ConstantPolicy(-1))
    metrics = compute_metrics(result).metrics
    assert metrics['sharpe'].status == metrics['cagr'].status == 'not_applicable'


def test_profit_factor_and_calmar_edges():
    from indexpilot_us100.metrics import Metric, profit_factor, calmar_ratio
    assert profit_factor([100, -25, 50, -50, 0]).value == 2
    assert profit_factor([-20]).value == 0
    assert profit_factor([10]).status == 'positive_infinity'
    assert profit_factor([]).status == profit_factor([0]).status == 'undefined'
    assert calmar_ratio(Metric(.1), .2).value == .5
    assert calmar_ratio(Metric(.1), 0).status == 'positive_infinity'
    assert calmar_ratio(Metric(0), 0).status == 'undefined'
    metrics = compute_metrics(run_episode(market(), CashPolicy())).metrics
    assert set(metrics) == {'max_drawdown', 'sharpe', 'cagr', 'profit_factor', 'calmar'}
