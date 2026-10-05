import pytest
from indexpilot_us100.environment.trading import TradingEnvironment
from indexpilot_us100.portfolio.simulator import run_episode
from test_simulator import market, ConstantPolicy


def test_exact_simulator_adapter():
    env=TradingEnvironment(market())
    assert env.reset(42).exposure == 0
    trajectory=env.rollout(ConstantPolicy(.5))
    reference=run_episode(market(),ConstantPolicy(.5))
    assert trajectory.result.ledger == reference.ledger
    assert [t.reward for t in trajectory.transitions] == [i['reward'] for i in reference.intervals]
    assert trajectory.transitions[-1].terminated
    assert trajectory.transitions[-1].next_state is None
    assert not trajectory.transitions[0].terminated
    assert env.rollout(ConstantPolicy(.5)).result.ledger == reference.ledger


def test_rare_final_fee_and_action_validation():
    env=TradingEnvironment(market([100.]*22+[199.9,200.]))
    trajectory=env.rollout(ConstantPolicy(-1))
    assert len(trajectory.transitions)==1
    assert trajectory.transitions[0].reward == pytest.approx(trajectory.result.intervals[0]['net_return'])
    with pytest.raises(ValueError): env.rollout(ConstantPolicy(.1))
