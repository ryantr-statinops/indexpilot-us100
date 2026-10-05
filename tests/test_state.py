from dataclasses import replace
from datetime import date
import pytest
from indexpilot_us100.agents.state import STATE_COUNT, encode_state, observation_vector
from indexpilot_us100.portfolio.market import MarketFeatures
from indexpilot_us100.portfolio.simulator import Observation


def observation():
    return Observation(21,date(2020,1,1),MarketFeatures(0,0,0,.02,100,100),100000,0,100000,0,0)


def test_bins_are_fixed_and_causal():
    obs=observation()
    assert STATE_COUNT == 3840
    assert 0 <= encode_state(obs) < STATE_COUNT
    assert encode_state(replace(obs,index=999,date=date(2025,1,1))) == encode_state(obs)
    assert observation_vector(obs).dtype.name == 'float64'
    assert encode_state(replace(obs,exposure=-20)) != encode_state(replace(obs,exposure=20))
    with pytest.raises(ValueError): encode_state(replace(obs,exposure=float('nan')))
    with pytest.raises(ValueError): encode_state(replace(obs,drawdown=1))
