from dataclasses import replace
from final_helpers import source_fixture
from indexpilot_us100.evaluation.final.protocol import prepare_protocol
from indexpilot_us100.evaluation.final.workflow import run_evaluation
from indexpilot_us100.evaluation.final.report import generate_report


def test_report_reads_artifacts_without_policy_calls(tmp_path,monkeypatch):
    data,source,config=source_fixture(tmp_path);root=tmp_path/'final'
    prepare_protocol(data,source,replace(config,seeds=(42,),costs_bps=(10.,)),root);run_evaluation(root)
    def forbidden(*args): raise AssertionError('Report must not evaluate')
    monkeypatch.setattr('indexpilot_us100.evaluation.final.workflow.evaluate_scenario',forbidden)
    text=generate_report(root).read_text()
    assert '## 10.' in text and '2020-05-01' in text and 'N/A' in text
    assert generate_report(root,tmp_path/'REPORT.md').read_text()==text
