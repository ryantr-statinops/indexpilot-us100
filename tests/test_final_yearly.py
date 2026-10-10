from datetime import date

import pytest

from indexpilot_us100.evaluation.final.yearly import yearly_summary


def test_year_boundary_compounds_without_reset():
    intervals = [
        dict(date=date(2023, 12, 28), end_date=date(2023, 12, 29), net_return=0.1, fees=2),
        dict(date=date(2023, 12, 29), end_date=date(2024, 1, 2), net_return=-0.1, fees=3),
    ]
    decisions = [dict(target=1.0), dict(target=0.0)]
    events = [dict(holdings=10), dict(holdings=0)]
    rows = yearly_summary(
        dict(scenario_id="x"),
        intervals,
        decisions,
        events,
        [dict(exit_date=date(2024, 1, 2))],
        dict(evaluation_config=dict(test_start="2023-01-01", test_end="2024-01-02")),
        {
            2023: dict(start_date=date(2023, 12, 28), end_date=date(2023, 12, 29)),
            2024: dict(start_date=date(2023, 12, 29), end_date=date(2024, 1, 2)),
        },
    )
    assert (1 + rows[0]["net_return"]) * (1 + rows[1]["net_return"]) - 1 == pytest.approx(-0.01)
    assert sum(row["fees"] for row in rows) == 5
    assert rows[0]["closed_trades"] == 0 and rows[1]["closed_trades"] == 1
    assert not rows[0]["partial_year"] and rows[1]["partial_year"]


@pytest.mark.parametrize(
    "actual_end,partial", [(date(2023, 12, 10), True), (date(2023, 12, 29), False)]
)
def test_december_early_termination_uses_intended_session(actual_end, partial):
    intervals = [
        dict(
            date=date(2023, 1, 3),
            end_date=actual_end,
            net_return=-1.1 if partial else 0.1,
            fees=4.0,
        )
    ]
    result = yearly_summary(
        dict(scenario_id="x"),
        intervals,
        [dict(target=-0.5)],
        [dict(holdings=-1)],
        [dict(exit_date=actual_end)],
        dict(evaluation_config=dict(test_start="2023-01-01", test_end="2023-12-31")),
        {2023: dict(start_date=date(2023, 1, 3), end_date=date(2023, 12, 29))},
    )
    assert result[0]["partial_year"] == partial
    assert result[0]["expected_end_date"] == "2023-12-29"
    assert result[0]["fees"] == 4.0


def test_expected_years_follow_market_intervals_and_warmup():
    from datetime import timedelta

    import numpy as np

    from indexpilot_us100.evaluation.final.yearly import expected_yearly_coverage
    from indexpilot_us100.portfolio import MarketData, SimulationConfig

    dates = tuple(date(2023, 11, 29) + timedelta(days=i) for i in range(21)) + (
        date(2023, 12, 28),
        date(2023, 12, 29),
        date(2024, 1, 2),
    )
    market = MarketData(dates, np.ones(len(dates)) * 100, np.ones(len(dates)) * 100)
    coverage = expected_yearly_coverage(market, SimulationConfig())
    assert coverage[2023] == dict(start_date=date(2023, 12, 28), end_date=date(2023, 12, 29))
    assert coverage[2024] == dict(start_date=date(2023, 12, 29), end_date=date(2024, 1, 2))
