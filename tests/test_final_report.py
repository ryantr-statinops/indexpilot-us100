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


def test_report_section_composition_and_optional_figures(tmp_path):
    from indexpilot_us100.evaluation.final import report
    data,source,config=source_fixture(tmp_path);root=tmp_path/'final'
    prepare_protocol(data,source,replace(config,seeds=(42,),costs_bps=(10.,)),root);run_evaluation(root)
    context=report.load_report_context(root)
    sections=[report.research_section,report.data_section,report.simulation_section,report.learning_section,report.protocol_section,report.primary_results_section,report.robustness_section,report.yearly_section,report.conclusions_section,report.reproduction_section]
    expected='\n\n'.join(['# Báo cáo hoàn thiện prototype AAPL',*[section(context) for section in sections]])+'\n'
    assert generate_report(root).read_text()==expected
    (root/'figures').mkdir();(root/'figures/example.png').write_bytes(b'png')
    assert '![example](figures/example.png)' in generate_report(root).read_text()
    assert generate_report(root,tmp_path/'export.md').read_text()==expected
