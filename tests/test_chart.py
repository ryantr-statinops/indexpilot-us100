import json
import sys
import polars as pl
from indexpilot_us100.evaluation.chart import load_chart_series
from indexpilot_us100.evaluation.export import export_results
from indexpilot_us100.portfolio.baselines import CashPolicy
from indexpilot_us100.portfolio.simulator import run_episode
from test_market import frame
from test_simulator import market


def test_chart_adapter_without_gui(tmp_path):
    source = tmp_path / 'source.parquet'
    frame().write_parquet(source)
    result = run_episode(market(), CashPolicy())
    export_results([result], source, tmp_path / 'run')
    series = load_chart_series(tmp_path / 'run')
    assert len(series) == 1
    assert len(series[0]['times']) == len(result.equity)
    assert list(series[0]['equity']) == [100000] * len(result.equity)
    assert list(series[0]['drawdown']) == [0] * len(result.equity)
    assert 'finplot' not in sys.modules


def test_missing_optional_dependency(monkeypatch):
    import pytest
    from indexpilot_us100.evaluation.chart import create_chart
    monkeypatch.setitem(sys.modules, 'finplot', None)
    with pytest.raises(RuntimeError, match='uv sync'):
        create_chart([])
