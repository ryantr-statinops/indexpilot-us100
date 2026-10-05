from dataclasses import replace
import json
import pytest
from final_helpers import source_fixture
from indexpilot_us100.evaluation.final.protocol import prepare_protocol
from indexpilot_us100.evaluation.final.workflow import run_evaluation,verify_evaluation
from indexpilot_us100.evaluation.final.cli import main


def test_run_cache_verify_and_tamper(tmp_path,monkeypatch):
    data,source,config=source_fixture(tmp_path)
    root=tmp_path/'final'; prepare_protocol(data,source,replace(config,seeds=(42,),costs_bps=(10.,)),root)
    result=run_evaluation(root)
    assert len(result['scenarios'])==8
    replay=verify_evaluation(root)
    assert json.loads((replay/'verification.json').read_text())['status']=='verified'
    monkeypatch.setattr('indexpilot_us100.evaluation.final.workflow.evaluate_scenario',lambda *a:pytest.fail('cached run must not evaluate'))
    assert run_evaluation(root)==result
    (root/'primary_summary.csv').write_text('tampered')
    with pytest.raises(ValueError,match='summary integrity'): run_evaluation(root)


def test_cli_errors_are_clear(tmp_path):
    with pytest.raises(SystemExit) as error: main(['run','--protocol-dir',str(tmp_path)])
    assert error.value.code==2
