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
