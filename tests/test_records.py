from datetime import date

import pytest

from indexpilot_us100.portfolio.account import Account, TargetExposure, rebalance
from indexpilot_us100.portfolio.records import account_event, order_record


def test_events_reconcile():
    after, order = rebalance(Account(100000), 100, TargetExposure(-0.5), 0.001)
    record = order_record(1, date(2020, 1, 1), order)
    assert record["cash_after"] - record["cash_before"] == pytest.approx(
        -record["delta_units"] * 100 - record["fee"]
    )
    event = account_event(2, date(2020, 1, 2), "mark", after, 120)
    assert event["equity"] == event["cash"] + event["holdings"] * event["price"]
