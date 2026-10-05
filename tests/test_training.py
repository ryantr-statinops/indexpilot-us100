from dataclasses import replace
import numpy as np
from indexpilot_us100.agents.config import LearningConfig
from indexpilot_us100.agents.training import chronological_segments, run_experiments
from indexpilot_us100.portfolio.config import SimulationConfig
from test_reconciliation import synthetic_market


def config():
    return LearningConfig(episodes=2,lambdas=(0.,.5),train_end='2020-03-10',validation_start='2020-03-11',validation_end='2020-04-30',test_start='2020-05-01')


def test_split_and_repeated_learning():
    data=synthetic_market()
    simulation=SimulationConfig()
    train,validation=chronological_segments(data,config(),simulation)
    assert train.dates[-1].isoformat()=='2020-03-10'
    assert validation.dates[21].isoformat()=='2020-03-11'
    first,selection=run_experiments(data,simulation,config())
    second,again=run_experiments(data,simulation,config())
    assert selection==again and not selection['test_evaluated']
    for a,b in zip(first,second):
        np.testing.assert_array_equal(a.agent.q,b.agent.q)
        assert a.training_log==b.training_log
        assert a.validation.result.orders==b.validation.result.orders
        assert a.validation.result.equity[0]['date'].isoformat()=='2020-03-11'
        assert a.agent.visits.sum()==sum(row['transition_count'] for row in a.training_log)
        assert a.agent.epsilon==0


def test_reserved_test_values_never_change_learning():
    from indexpilot_us100.portfolio.market import MarketData
    data=synthetic_market()
    opens,closes=data.opens.copy(),data.closes.copy()
    opens[121:]*=20; closes[121:]*=.01
    altered=MarketData(data.dates,opens,closes,data.warnings)
    first,selection=run_experiments(data,SimulationConfig(),config())
    second,again=run_experiments(altered,SimulationConfig(),config())
    assert selection==again
    for a,b in zip(first,second):
        np.testing.assert_array_equal(a.agent.q,b.agent.q)
        assert a.validation.result.ledger==b.validation.result.ledger


def test_validation_prices_do_not_fit_q_table():
    from indexpilot_us100.portfolio.market import MarketData
    data=synthetic_market()
    opens,closes=data.opens.copy(),data.closes.copy()
    opens[70:121]*=2; closes[70:121]*=.5
    changed=MarketData(data.dates,opens,closes,data.warnings)
    first,_=run_experiments(data,SimulationConfig(),config())
    second,_=run_experiments(changed,SimulationConfig(),config())
    for a,b in zip(first,second):
        np.testing.assert_array_equal(a.agent.q,b.agent.q)
        np.testing.assert_array_equal(a.agent.visits,b.agent.visits)
        assert a.training_log==b.training_log


def test_undefined_validation_does_not_invent_a_winner():
    from indexpilot_us100.portfolio.market import MarketData
    data=synthetic_market()
    flat=MarketData(data.dates,np.full(len(data.dates),100.),np.full(len(data.dates),100.),data.warnings)
    experiments,selection=run_experiments(flat,SimulationConfig(),config())
    assert selection['selected_lambda']==0
    assert selection['status']=='undefined_fallback_lambda_zero'
    np.testing.assert_array_equal(experiments[0].agent.q,experiments[1].agent.q)
