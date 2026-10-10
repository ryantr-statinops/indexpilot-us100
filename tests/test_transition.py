import pytest

from indexpilot_us100.portfolio.account import Account, TargetExposure
from indexpilot_us100.portfolio.transition import advance_interval


@pytest.mark.parametrize("target", [-1, -0.5, 0, 0.5, 1])
def test_one_interval(target):
    result = advance_interval(Account(100000), 100, 110, TargetExposure(target))
    assert result.gross_pnl == pytest.approx(10000 * target)
    assert result.net_return == pytest.approx(0.1 * target)


def test_flat_price_fees():
    result = advance_interval(Account(100000), 100, 100, TargetExposure(1), 0.001)
    assert result.gross_pnl == 0
    assert result.end_equity == pytest.approx(100000 - result.execution.fee)


def test_reward_cost_once():
    from indexpilot_us100.portfolio.transition import interval_reward

    interval = advance_interval(Account(100000), 100, 110, TargetExposure(0.5), 0.001)
    zero = interval_reward(interval, 0.02)
    penalized = interval_reward(interval, 0.02, 2)
    assert zero.value == pytest.approx(interval.net_return)
    assert penalized.value == pytest.approx(zero.value - 2 * zero.risk)
    assert interval_reward(interval, 0.02, closing_fee=50).value == pytest.approx(
        zero.value - 0.0005
    )


def test_finalization_and_insolvency():
    from indexpilot_us100.portfolio.transition import liquidate

    result = liquidate(Account(0, 1000), 110, 0.001)
    assert result.account.cash == 109890
    assert result.account.holdings == 0
    assert result.status == "completed"
    failed = liquidate(Account(200000, -1000), 210, 0.001)
    assert failed.account.cash == -10210
    assert failed.account.exposure(210) is None
    assert failed.status == "insolvent"
