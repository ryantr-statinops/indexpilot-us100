import sys

from test_market import frame
from test_simulator import market

from indexpilot_us100.evaluation import export_results, load_chart_series
from indexpilot_us100.portfolio import CashPolicy, run_episode


def test_chart_adapter_without_gui(tmp_path, monkeypatch):
    monkeypatch.setitem(sys.modules, "finplot", None)
    source = tmp_path / "source.parquet"
    frame().write_parquet(source)
    result = run_episode(market(), CashPolicy())
    export_results([result], source, tmp_path / "run")
    series = load_chart_series(tmp_path / "run")
    assert len(series) == 1
    assert len(series[0]["times"]) == len(result.equity)
    assert list(series[0]["equity"]) == [100000] * len(result.equity)
    assert list(series[0]["drawdown"]) == [0] * len(result.equity)
    assert sys.modules["finplot"] is None


def test_missing_optional_dependency(monkeypatch):
    import pytest

    from indexpilot_us100.evaluation import create_chart

    monkeypatch.setitem(sys.modules, "finplot", None)
    with pytest.raises(RuntimeError, match="uv sync"):
        create_chart([])
