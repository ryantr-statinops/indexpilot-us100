import polars as pl
from test_reconciliation import synthetic_market

from indexpilot_us100.agents.config import LearningConfig
from indexpilot_us100.agents.training import run_experiments
from indexpilot_us100.evaluation.final.config import EvaluationConfig
from indexpilot_us100.evaluation.learning_export import export_learning
from indexpilot_us100.portfolio.config import SimulationConfig


def source_fixture(tmp_path):
    data = synthetic_market()
    source = tmp_path / "data.parquet"
    pl.DataFrame(
        {"date": data.dates, "adj_open": data.opens, "adj_close": data.closes}
    ).write_parquet(source)
    learning = LearningConfig(
        episodes=1,
        lambdas=(0.0, 2.0),
        train_end="2020-03-10",
        validation_start="2020-03-11",
        validation_end="2020-04-30",
        test_start="2020-05-01",
    )
    simulation = SimulationConfig()
    experiments, selection = run_experiments(data, simulation, learning)
    # Fixture exercises provenance, not statistical model selection.
    selection.update(selected_lambda=2.0, selected_index=1, status="selected")
    root = tmp_path / "stage3"
    export_learning(experiments, selection, simulation, learning, source, root)
    config = EvaluationConfig(source_run=str(root), test_start="2020-05-01", test_end="2020-05-19")
    return source, root, config
