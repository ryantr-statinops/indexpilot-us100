import pytest
from test_simulator import market

from indexpilot_us100.portfolio import BuyHoldPolicy, CashPolicy, run_episode


def test_cash():
    result = run_episode(market(), CashPolicy())
    assert result.orders == result.trades == []
    assert all(row["equity"] == 100000 for row in result.equity)
    assert all(row["reward"] == 0 for row in result.intervals)


def test_buy_hold():
    policy = BuyHoldPolicy()
    result = run_episode(market(), policy)
    assert len(result.orders) == 2
    assert len(result.trades) == 1
    assert result.orders[0]["units_after"] == pytest.approx(result.orders[-1]["units_before"])
    assert result.equity == run_episode(market(), policy).equity


def test_fixed_exposure_rebalances():
    from indexpilot_us100.portfolio import FixedExposurePolicy

    for value in (0.5, -0.5):
        result = run_episode(market(), FixedExposurePolicy(value, "fixed"))
        assert len(result.orders) == 4
        for event in result.ledger:
            if event["kind"] == "execution":
                assert event["exposure"] == pytest.approx(value)
        assert result.orders[1]["delta_units"] != 0


def test_sma_and_random():
    from indexpilot_us100.portfolio import RandomPolicy, SMAPolicy, baseline_policies

    sma = run_episode(market(), SMAPolicy())
    assert sma.orders[0]["date"] == market().dates[23]
    random = RandomPolicy()
    assert run_episode(market(), random).orders == run_episode(market(), random).orders
    assert len(baseline_policies()) == 6
