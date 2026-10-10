import pytest

from indexpilot_us100.portfolio import Account


def test_valuation():
    assert Account(50000, 500).equity(100) == 100000
    assert Account(150000, -500).exposure(100) == -0.5
    assert Account(100000).exposure(100) == 0
    assert Account(100, -2).exposure(100) is None
    with pytest.raises(ValueError):
        Account(100).equity(0)
    with pytest.raises(ValueError):
        Account(float("nan"))


def test_free_rebalance_and_hold():
    from indexpilot_us100.portfolio import HoldPosition, TargetExposure, rebalance

    account = Account(100000)
    for target in (-1.0, -0.5, 0.0, 0.5, 1.0):
        after, execution = rebalance(account, 100.0, TargetExposure(target))
        assert after.exposure(100) == pytest.approx(target)
        assert after.equity(100) == 100000
        held, _ = rebalance(after, 120, HoldPosition())
        assert held == after
    for target in (-1.01, 1.01, float("nan")):
        with pytest.raises(ValueError):
            TargetExposure(target)


def test_costed_target_and_hand_example():
    from indexpilot_us100.portfolio import TargetExposure, rebalance

    after, order = rebalance(Account(100000), 100, TargetExposure(1), 0.001)
    assert order.traded_notional == pytest.approx(99900.0999001)
    assert order.fee == pytest.approx(99.9000999)
    assert after.cash == pytest.approx(0, abs=1e-8)
    closed, exit_order = rebalance(after, 110, TargetExposure(0), 0.001)
    assert closed.equity(110) == pytest.approx(109780.2197802)
    assert exit_order.fee == pytest.approx(109.89010989)


@pytest.mark.parametrize("old", [-1, -0.5, 0, 0.5, 1])
@pytest.mark.parametrize("new", [-1, -0.5, 0, 0.5, 1])
def test_costed_reversals(old, new):
    from indexpilot_us100.portfolio import TargetExposure, rebalance

    account = Account(100000 - old * 100000, old * 1000)
    after, order = rebalance(account, 100, TargetExposure(new), 0.001)
    assert after.exposure(100) == pytest.approx(new)
    assert after.equity(100) == pytest.approx(100000 - order.fee)
    assert order.fee == pytest.approx(0.001 * abs(order.delta_units) * 100)
