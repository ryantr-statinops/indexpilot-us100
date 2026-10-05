from datetime import date, timedelta
import polars as pl
import pytest
from indexpilot_us100.portfolio.market import MarketData
from indexpilot_us100.portfolio.account import TargetExposure, HoldPosition
from indexpilot_us100.portfolio.config import SimulationConfig
from indexpilot_us100.portfolio.simulator import run_episode


class ConstantPolicy:
    name = 'constant'
    def __init__(self, target=.5): self.target = target
    def reset(self, seed): pass
    def decide(self, observation): return TargetExposure(self.target)


def market(prices=None):
    prices = prices or [100.] * 21 + [100., 110., 105., 120.]
    return MarketData.from_frame(pl.DataFrame({'date': [date(2020, 1, 1) + timedelta(days=i) for i in range(len(prices))], 'adj_open': prices, 'adj_close': prices}))


def test_full_episode():
    result = run_episode(market(), ConstantPolicy())
    assert len(result.intervals) == 3
    assert result.equity[-1]['holdings'] == 0
    assert sum(t['net_pnl'] for t in result.trades) == pytest.approx(result.equity[-1]['equity'] - 100000)
    assert len(result.trades) == 1
    assert result.equity == run_episode(market(), ConstantPolicy()).equity
    assert result.orders[-1]['kind'] == 'liquidation'
    assert len(result.equity) == len(result.intervals) + 1
    for item in result.intervals:
        assert item['reward'] == pytest.approx(item['net_return'])


def test_insolvency():
    result = run_episode(market([100.] * 22 + [300., 400.]), ConstantPolicy(-1))
    assert result.status == 'insolvent'
    assert len(result.intervals) == 1
    assert result.equity[-1]['equity'] < 0
    assert result.equity[-1]['holdings'] == 0
    assert result.ledger[-1]['exposure'] is None
