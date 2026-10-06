"""Typed record contracts must preserve the existing dictionary wire format."""
import json
from typing import get_type_hints
from indexpilot_us100.evaluation.final.types import Scenario,ModelInventory,Coverage,ScoreRow,RunManifest
from indexpilot_us100.evaluation.final.runner import EvaluatedRun
from indexpilot_us100.portfolio.simulator import SimulationResult


def test_types_remain_plain_json_dictionaries():
    scenario=Scenario(kind='rl',policy='q_lambda_2',seed=42,risk_lambda=2.,cost_bps=10.,scenario_id='example')
    coverage=Coverage(start_date='2023-01-03',end_date='2026-10-02',interval_count=940)
    row=ScoreRow(**scenario,net_return=0.,sharpe=None,sharpe_status='undefined')
    assert type(scenario) is dict and type(row) is dict
    assert json.loads(json.dumps(row,allow_nan=False))==row
    assert set(coverage)=={'start_date','end_date','interval_count'}
    assert 'models' not in RunManifest.__annotations__
    assert 'sha256' in ModelInventory.__annotations__
    assert get_type_hints(EvaluatedRun)['result'] is SimulationResult
