from dataclasses import asdict
import json
from pathlib import Path
import subprocess
import sys
import polars as pl
from indexpilot_us100.evaluation.learning_cli import main
from test_reconciliation import synthetic_market


def test_train_cli(tmp_path,capsys):
    data=synthetic_market()
    source=tmp_path/'data.parquet'
    pl.DataFrame({'date':data.dates,'adj_open':data.opens,'adj_close':data.closes}).write_parquet(source)
    config=tmp_path/'config.toml'
    config.write_text('[learning]\nepisodes=1\nlambdas=[0]\ntrain_end="2020-03-10"\nvalidation_start="2020-03-11"\nvalidation_end="2020-04-30"\ntest_start="2020-05-01"\n')
    output=tmp_path/'run'
    assert main(['--data',str(source),'--config',str(config),'--output-dir',str(output),'--quiet'])==0
    assert 'was not evaluated' in capsys.readouterr().out
    assert json.loads((output/'run_manifest.json').read_text())['test_evaluated'] is False
    executable=Path(sys.executable).parent/'indexpilot-train'
    assert subprocess.run([str(executable),'--help'],capture_output=True).returncode==0
