from dataclasses import replace

import pytest
from final_helpers import source_fixture

from indexpilot_us100.evaluation.final import generate_report, prepare_protocol, run_evaluation


def test_report_reads_artifacts_without_policy_calls(tmp_path, monkeypatch):
    data, source, config = source_fixture(tmp_path)
    root = tmp_path / "final"
    prepare_protocol(data, source, replace(config, seeds=(42,), costs_bps=(10.0,)), root)
    run_evaluation(root)

    def forbidden(*args):
        raise AssertionError("Report must not evaluate")

    monkeypatch.setattr("indexpilot_us100.evaluation.final.workflow.evaluate_scenario", forbidden)
    text = generate_report(root).read_text()
    assert "## 10." in text and "2020-05-01" in text and "N/A" in text
    assert generate_report(root, tmp_path / "REPORT.md").read_text() == text


def test_report_section_composition_and_optional_figures(tmp_path):
    from indexpilot_us100.evaluation.final import report

    data, source, config = source_fixture(tmp_path)
    root = tmp_path / "final"
    prepare_protocol(data, source, replace(config, seeds=(42,), costs_bps=(10.0,)), root)
    run_evaluation(root)
    context = report.load_report_context(root)
    sections = [
        report.research_section,
        report.data_section,
        report.simulation_section,
        report.learning_section,
        report.protocol_section,
        report.primary_results_section,
        report.robustness_section,
        report.yearly_section,
        report.conclusions_section,
        report.reproduction_section,
    ]
    expected = (
        "\n\n".join(
            [
                f"# Evaluation report: {context.instrument_label}",
                *[section(context) for section in sections],
            ]
        )
        + "\n"
    )
    assert generate_report(root).read_text() == expected
    (root / "figures").mkdir()
    (root / "figures/example.png").write_bytes(b"png")
    assert "![example](figures/example.png)" in generate_report(root).read_text()
    assert generate_report(root, tmp_path / "export.md").read_text() == expected


@pytest.mark.parametrize("label", [None, "QQQ / Nasdaq-100 ETF"])
def test_report_identity_is_not_hardcoded(tmp_path, label):
    from indexpilot_us100.evaluation.final import load_report_context
    from indexpilot_us100.evaluation.final.report import research_section

    data, source, config = source_fixture(tmp_path)
    root = tmp_path / "report"
    prepare_protocol(
        data, source, replace(config, instrument_label=label, seeds=(42,), costs_bps=(10.0,)), root
    )
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

        context = load_report_context(root)
        assert replace(context, protocol=protocol).instrument_label == "Single-asset experiment"


def test_report_replay_commands_use_actual_paths(tmp_path):
    import shlex

    from indexpilot_us100.evaluation.final import load_report_context
    from indexpilot_us100.evaluation.final.report import reproduction_section

    data, source, config = source_fixture(tmp_path)
    root = tmp_path / "QQQ run with spaces"
    prepare_protocol(data, source, replace(config, seeds=(42,), costs_bps=(10.0,)), root)
    run_evaluation(root)
    context = load_report_context(root)
    rendering_protocol = {
        **context.protocol,
        "evaluation_config": {**context.config, "primary_cost_bps": 20.0, "primary_lambda": 0.5},
    }
    text = reproduction_section(replace(context, protocol=rendering_protocol))
    commands = [shlex.split(line) for line in text.splitlines() if line.startswith("uv run ")]
    for command in commands:
        key = "--run-dir" if "indexpilot-chart" in command else "--protocol-dir"
        assert command[command.index(key) + 1] == str(root.resolve())
        if "--data" in command:
            assert command[command.index("--data") + 1] == str(data.resolve())
    seed_command = commands[-1]
    assert seed_command[seed_command.index("--cost-bps") + 1] == "20"
    assert seed_command[seed_command.index("--risk-lambda") + 1] == "0.5"
    assert "aapl" not in text.lower()
    assert "prepare --data" not in text


def test_report_outlook_is_single_asset(tmp_path):
    from indexpilot_us100.evaluation.final import load_report_context
    from indexpilot_us100.evaluation.final.report import reproduction_section

    data, source, config = source_fixture(tmp_path)
    root = tmp_path / "outlook"
    prepare_protocol(data, source, replace(config, seeds=(42,), costs_bps=(10.0,)), root)
    run_evaluation(root)
    text = reproduction_section(load_report_context(root))
    assert "Future single-asset research" in text
    assert "walk-forward" in text
    assert "multi-asset" not in text
    assert "historical US100 universe" not in text
