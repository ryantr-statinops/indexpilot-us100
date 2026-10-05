import pytest
from indexpilot_us100.portfolio.account import Account, TargetExposure
from indexpilot_us100.portfolio.transition import advance_interval


@pytest.mark.parametrize('target', [-1, -.5, 0, .5, 1])
def test_one_interval(target):
    result = advance_interval(Account(100000), 100, 110, TargetExposure(target))
    assert result.gross_pnl == pytest.approx(10000 * target)
    assert result.net_return == pytest.approx(.1 * target)


def test_flat_price_fees():
    result = advance_interval(Account(100000), 100, 100, TargetExposure(1), .001)
    assert result.gross_pnl == 0
    assert result.end_equity == pytest.approx(100000 - result.execution.fee)


def test_reward_cost_once():
    from indexpilot_us100.portfolio.transition import interval_reward
    interval = advance_interval(Account(100000), 100, 110, TargetExposure(.5), .001)
    zero = interval_reward(interval, .02)
    penalized = interval_reward(interval, .02, 2)
    assert zero.value == pytest.approx(interval.net_return)
    assert penalized.value == pytest.approx(zero.value - 2 * zero.risk)
    assert interval_reward(interval, .02, closing_fee=50).value == pytest.approx(zero.value - .0005)
