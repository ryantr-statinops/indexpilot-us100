from dataclasses import replace
import pytest
from indexpilot_us100.evaluation.final.protocol import prepare_protocol
from indexpilot_us100.evaluation.final.matrix import scenarios,evaluate_scenario
from indexpilot_us100.evaluation.final.windows import build_test_segment
from indexpilot_us100.evaluation.final.artifacts import store_run,check_run
from indexpilot_us100.portfolio.market import load_market_data
from indexpilot_us100.portfolio.config import SimulationConfig
from final_helpers import source_fixture


def test_atomic_scenario_roundtrip(tmp_path):
    data,source,config=source_fixture(tmp_path);config=replace(config,seeds=(42,),costs_bps=(10.,))
    root=tmp_path/'frozen';protocol=prepare_protocol(data,source,config,root)
    segment=build_test_segment(load_market_data(data),config,SimulationConfig())
    run=evaluate_scenario(root,protocol,segment,scenarios(protocol)[0])
    row=store_run(root,protocol,run)
    target=root/'runs'/run.scenario['scenario_id']
    assert check_run(target,protocol['protocol_id'])==row
    assert store_run(root,protocol,run)==row
    assert row['intended_start_date']=='2020-05-01'
    (target/'score.json').write_text('{}')
    with pytest.raises(ValueError,match='integrity'): check_run(target,protocol['protocol_id'])
