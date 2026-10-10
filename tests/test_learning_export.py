import json

import numpy as np
import polars as pl
import pytest
from test_reconciliation import synthetic_market
from test_training import config

from indexpilot_us100.agents.qlearning import QLearningAgent
from indexpilot_us100.agents.training import run_experiments
from indexpilot_us100.evaluation.learning_export import export_learning
from indexpilot_us100.portfolio.config import SimulationConfig


def test_model_artifacts(tmp_path):
    data = synthetic_market()
    simulation = SimulationConfig()
    learning = config()
    experiments, selection = run_experiments(data, simulation, learning)
    source = tmp_path / "source.parquet"
    pl.DataFrame({"x": [1]}).write_parquet(source)
    root = tmp_path / "run"
    export_learning(experiments, selection, simulation, learning, source, root)
    manifest = json.loads((root / "run_manifest.json").read_text())
    assert not manifest["test_evaluated"]
    assert pl.read_csv(root / "validation_summary.csv").height == 14
    assert pl.read_parquet(root / "lambda_0/validation_transitions.parquet")["terminated"][-1]
    restored = QLearningAgent.load(root / "lambda_0/model.npz")
    np.testing.assert_array_equal(restored.q, experiments[0].agent.q)
    assert (
        json.loads((root / "diagnostics.json").read_text())["lambda_0/validation"]["interval_count"]
        > 0
    )
    with pytest.raises(ValueError):
        export_learning(experiments, selection, simulation, learning, source, root)


def test_destination_is_checked_before_training(tmp_path):
    from indexpilot_us100.evaluation.learning_export import validate_learning_destination

    foreign = tmp_path / "foreign"
    foreign.mkdir()
    (foreign / "important").write_text("keep")
    with pytest.raises(ValueError, match="Refusing"):
        validate_learning_destination(tmp_path / "source.parquet", foreign, True)
    assert (foreign / "important").read_text() == "keep"
    with pytest.raises(ValueError, match="contain input"):
        validate_learning_destination(
            tmp_path / "protected" / "source.parquet", tmp_path / "protected", True
        )


def test_selected_model_chart_adapter(tmp_path):
    from indexpilot_us100.evaluation.chart import load_chart_series

    experiments, selection = run_experiments(synthetic_market(), SimulationConfig(), config())
    source = tmp_path / "source.parquet"
    pl.DataFrame({"x": [1]}).write_parquet(source)
    export_learning(experiments, selection, SimulationConfig(), config(), source, tmp_path / "run")
    series = load_chart_series(tmp_path / "run")
    assert len(series) == 7
    assert series[-1]["name"] == experiments[selection["selected_index"]].agent.name
