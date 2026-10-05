import json
import polars as pl
import pytest
from indexpilot_us100.evaluation.export import export_results
from indexpilot_us100.portfolio.baselines import baseline_policies
from indexpilot_us100.portfolio.simulator import run_episode
from test_simulator import market


def test_export_roundtrip(tmp_path):
    input_path = tmp_path / 'source.parquet'
    pl.DataFrame({'x': [1]}).write_parquet(input_path)
    results = [run_episode(market(), policy) for policy in baseline_policies()]
    output = tmp_path / 'run'
    export_results(results, input_path, output)
    summary = json.loads((output / 'summary.json').read_text())
    assert len(summary) == 6
    assert summary[0]['sharpe'] is None
    assert summary[0]['sharpe_status'] == 'undefined'
    assert pl.read_parquet(output / 'cash/orders.parquet').schema['date'] == pl.Date
    assert pl.read_parquet(output / 'buy_hold/equity.parquet')['equity'].to_list() == [row['equity'] for row in results[1].equity]
    with pytest.raises(ValueError, match='Output exists'):
        export_results(results, input_path, output)
    export_results(results, input_path, output, overwrite=True)
    foreign = tmp_path / 'foreign'
    foreign.mkdir()
    (foreign / 'file').write_text('keep')
    with pytest.raises(ValueError, match='Refusing'):
        export_results(results, input_path, foreign, overwrite=True)
    assert (foreign / 'file').read_text() == 'keep'


def test_repeat_exports_have_identical_numbers(tmp_path):
    source = tmp_path / 'source.parquet'
    pl.DataFrame({'x': [1]}).write_parquet(source)
    results = [run_episode(market(), policy) for policy in baseline_policies()]
    for directory in ('one', 'two'):
        export_results(results, source, tmp_path / directory)
    for filename in ('summary.csv', 'summary.json', 'buy_hold/equity.parquet', 'random_discrete/trades.parquet'):
        assert (tmp_path / 'one' / filename).read_bytes() == (tmp_path / 'two' / filename).read_bytes()
    manifest = json.loads((tmp_path / 'one/run_manifest.json').read_text())
    from indexpilot_us100.evaluation.export import file_hash
    assert manifest['input_sha256'] == file_hash(source)
    assert manifest['configuration']['seed'] == 42
