import pytest
from indexpilot_us100.portfolio.account import Account


def test_valuation():
    assert Account(50000, 500).equity(100) == 100000
    assert Account(150000, -500).exposure(100) == -.5
    assert Account(100000).exposure(100) == 0
    assert Account(100, -2).exposure(100) is None
    with pytest.raises(ValueError):
        Account(100).equity(0)
    with pytest.raises(ValueError):
        Account(float('nan'))


def test_free_rebalance_and_hold():
    from indexpilot_us100.portfolio.account import TargetExposure, HoldPosition, rebalance
    account = Account(100000)
    for target in (-1., -.5, 0., .5, 1.):
        after, execution = rebalance(account, 100., TargetExposure(target))
        assert after.exposure(100) == pytest.approx(target)
        assert after.equity(100) == 100000
        held, _ = rebalance(after, 120, HoldPosition())
        assert held == after
    for target in (-1.01, 1.01, float('nan')):
        with pytest.raises(ValueError):
            TargetExposure(target)
