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


def test_manifest_failure_resumes_without_replaying_scenarios(tmp_path,monkeypatch):
    data,source,config=source_fixture(tmp_path);root=tmp_path/'final'
    prepare_protocol(data,source,replace(config,seeds=(42,),costs_bps=(10.,)),root)
    from indexpilot_us100.evaluation import export
    from indexpilot_us100.evaluation.final import workflow
    original=export.os.replace
    def interrupted(source,target):
        raise OSError('manifest publication interrupted')
    monkeypatch.setattr(export.os,'replace',interrupted)
    with pytest.raises(OSError,match='interrupted'):run_evaluation(root)
    assert not (root/'run_manifest.json').exists()
    assert not list(root.glob('.run_manifest.json-*'))
    assert len(list((root/'runs').iterdir()))==8
    monkeypatch.setattr(export.os,'replace',original)
    monkeypatch.setattr(workflow,'evaluate_scenario',lambda *args:pytest.fail('completed scenarios must be reused'))
    assert len(run_evaluation(root)['scenarios'])==8
    (root/'run_manifest.json').write_text('{')
    with pytest.raises(ValueError):run_evaluation(root)


def test_atomic_json_preserves_destination_on_failure(tmp_path,monkeypatch):
    from indexpilot_us100.evaluation import export
    path=tmp_path/'manifest.json';path.write_text('{"old": true}')
    def fail(*args):raise OSError('replace failed')
    monkeypatch.setattr(export.os,'replace',fail)
    with pytest.raises(OSError):export.write_json_atomic(path,{'new':True})
    assert json.loads(path.read_text())=={'old':True}
    assert sorted(p.name for p in tmp_path.iterdir())==['manifest.json']


def test_completed_manifest_recovers_missing_ledger_event(tmp_path,monkeypatch):
    data,source,config=source_fixture(tmp_path);root=tmp_path/'final'
    prepare_protocol(data,source,replace(config,seeds=(42,),costs_bps=(10.,)),root)
    from indexpilot_us100.evaluation.final.history import ExperimentLedger
    from indexpilot_us100.evaluation.final.workflow import ledger_for
    original=ExperimentLedger.append
    def fail_completion(self,event,*args,**kwargs):
        if event=='completed':raise OSError('interrupted before completed event')
        return original(self,event,*args,**kwargs)
    monkeypatch.setattr(ExperimentLedger,'append',fail_completion)
    with pytest.raises(OSError):run_evaluation(root)
    assert (root/'run_manifest.json').exists()
    monkeypatch.setattr(ExperimentLedger,'append',original)
    assert len(run_evaluation(root)['scenarios'])==8
    assert ledger_for(root).events()[-1]['details']['recovered']
    with pytest.raises(ValueError,match='reason'):ledger_for(root).require_new_reason(None)
