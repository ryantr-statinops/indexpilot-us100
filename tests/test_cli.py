import polars as pl
import pytest
from indexpilot_us100.evaluation.cli import main
from test_market import frame


def test_cli(tmp_path, capsys):
    data = tmp_path / 'data.parquet'
    frame().write_parquet(data)
    config = tmp_path / 'config.toml'
    config.write_text('cost_bps = 10\n')
    output = tmp_path / 'run'
    assert main(['--data', str(data), '--config', str(config), '--output-dir', str(output)]) == 0
    assert 'buy_hold' in capsys.readouterr().out
    assert pl.read_csv(output / 'summary.csv').height == 6
    with pytest.raises(SystemExit) as error:
        main(['--data', str(data), '--config', str(config), '--output-dir', str(output)])
    assert error.value.code == 2
