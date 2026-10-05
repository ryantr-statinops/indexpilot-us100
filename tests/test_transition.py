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
