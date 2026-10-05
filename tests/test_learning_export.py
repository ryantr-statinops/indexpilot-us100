import json
import numpy as np
import polars as pl
import pytest
from indexpilot_us100.agents.qlearning import QLearningAgent
from indexpilot_us100.agents.training import run_experiments
from indexpilot_us100.evaluation.learning_export import export_learning
from indexpilot_us100.portfolio.config import SimulationConfig
from test_training import config
from test_reconciliation import synthetic_market


def test_model_artifacts(tmp_path):
    data=synthetic_market(); simulation=SimulationConfig(); learning=config()
    experiments,selection=run_experiments(data,simulation,learning)
    source=tmp_path/'source.parquet'; pl.DataFrame({'x':[1]}).write_parquet(source)
    root=tmp_path/'run'; export_learning(experiments,selection,simulation,learning,source,root)
    manifest=json.loads((root/'run_manifest.json').read_text())
    assert not manifest['test_evaluated']
    assert pl.read_csv(root/'validation_summary.csv').height==14
    assert pl.read_parquet(root/'lambda_0/validation_transitions.parquet')['terminated'][-1]
    restored=QLearningAgent.load(root/'lambda_0/model.npz')
    np.testing.assert_array_equal(restored.q,experiments[0].agent.q)
    assert json.loads((root/'diagnostics.json').read_text())['lambda_0/validation']['interval_count']>0
    with pytest.raises(ValueError): export_learning(experiments,selection,simulation,learning,source,root)
