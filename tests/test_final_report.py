import pytest
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
    expected='\n\n'.join([f'# Evaluation report: {context.instrument_label}',*[section(context) for section in sections]])+'\n'
    assert generate_report(root).read_text()==expected
    (root/'figures').mkdir();(root/'figures/example.png').write_bytes(b'png')
    assert '![example](figures/example.png)' in generate_report(root).read_text()
    assert generate_report(root,tmp_path/'export.md').read_text()==expected


@pytest.mark.parametrize("label", [None, "QQQ / Nasdaq-100 ETF"])
def test_report_identity_is_not_hardcoded(tmp_path, label):
    from indexpilot_us100.evaluation.final.report import load_report_context, research_section
    data, source, config = source_fixture(tmp_path)
    root = tmp_path / "report"
    prepare_protocol(data, source, replace(config, instrument_label=label, seeds=(42,), costs_bps=(10.,)), root)
    run_evaluation(root)
    text = generate_report(root).read_text()
    expected = label or "Single-asset experiment"
    assert text.startswith(f"# Evaluation report: {expected}\n")
    scope = research_section(load_report_context(root))
    assert expected in scope
    assert "AAPL" not in scope
    if label is None:
        import json
        protocol_path = root / "protocol.json"
        protocol = json.loads(protocol_path.read_text())
        protocol["evaluation_config"].pop("instrument_label")
        from indexpilot_us100.evaluation.final.report import ReportContext
        context = load_report_context(root)
        assert replace(context, protocol=protocol).instrument_label == "Single-asset experiment"
