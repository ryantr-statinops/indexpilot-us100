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


def test_installed_entrypoint_and_errors(tmp_path):
    import subprocess
    import sys
    from pathlib import Path
    command = Path(sys.executable).parent / 'indexpilot-simulate'
    result = subprocess.run([str(command), '--help'], text=True, capture_output=True)
    assert result.returncode == 0
    assert '--output-dir' in result.stdout
    result = subprocess.run([str(command), '--data', 'missing.parquet', '--config', 'configs/stage-2.toml', '--output-dir', str(tmp_path / 'run')], text=True, capture_output=True)
    assert result.returncode == 2
    assert 'Traceback' not in result.stderr
