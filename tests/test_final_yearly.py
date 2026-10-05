from datetime import date
import pytest
from indexpilot_us100.evaluation.final.yearly import yearly_summary


def test_year_boundary_compounds_without_reset():
    intervals=[dict(date=date(2023,12,28),end_date=date(2023,12,29),net_return=.1,fees=2),dict(date=date(2023,12,29),end_date=date(2024,1,2),net_return=-.1,fees=3)]
    decisions=[dict(target=1.),dict(target=0.)]
    events=[dict(holdings=10),dict(holdings=0)]
    rows=yearly_summary(dict(scenario_id='x'),intervals,decisions,events,[dict(exit_date=date(2024,1,2))],dict(evaluation_config=dict(test_start='2023-01-01',test_end='2024-01-02')))
    assert (1+rows[0]['net_return'])*(1+rows[1]['net_return'])-1==pytest.approx(-.01)
    assert sum(row['fees'] for row in rows)==5
    assert rows[0]['closed_trades']==0 and rows[1]['closed_trades']==1
    assert not rows[0]['partial_year'] and rows[1]['partial_year']
