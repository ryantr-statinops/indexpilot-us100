from dataclasses import replace
import pytest
from indexpilot_us100.evaluation.final.windows import build_test_segment
from indexpilot_us100.evaluation.final.config import EvaluationConfig
from indexpilot_us100.portfolio.config import SimulationConfig
from test_reconciliation import synthetic_market


def test_test_warmup():
    config=EvaluationConfig(test_start='2020-05-01',test_end='2020-05-19')
    segment=build_test_segment(synthetic_market(),config,SimulationConfig())
    assert segment.dates[21].isoformat()=='2020-05-01'
    assert segment.dates[-1].isoformat()=='2020-05-19'
    for bad in (replace(config,test_start='2020-01-02'),replace(config,test_end='2020-06-01'),replace(config,test_start='2020-05-19',test_end='2020-05-20')):
        with pytest.raises(ValueError): build_test_segment(synthetic_market(),bad,SimulationConfig())
