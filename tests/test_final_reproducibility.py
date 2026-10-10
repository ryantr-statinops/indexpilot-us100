"""Replay, full-matrix, relocation, interruption and CLI verification."""

import json
import shutil
import subprocess
import sys
from dataclasses import replace

import numpy as np
import pytest
from final_helpers import source_fixture

from indexpilot_us100.evaluation import file_hash
from indexpilot_us100.evaluation.final import (
    prepare_protocol,
    run_evaluation,
    validate_protocol,
    verify_evaluation,
)
from indexpilot_us100.evaluation.final.workflow import ledger_for


def test_interrupted_run_resumes_only_unfinished_scenarios(tmp_path, monkeypatch):
    data, source, config = source_fixture(tmp_path)
    root = tmp_path / "final"
    prepare_protocol(data, source, replace(config, seeds=(42,), costs_bps=(10.0,)), root)
    from indexpilot_us100.evaluation.final import workflow

    original = workflow.evaluate_scenario
    calls = []

    def interrupted(*args):
        calls.append(args[-1]["scenario_id"])
        if len(calls) == 3:
            raise ValueError("synthetic interruption")
        return original(*args)

    monkeypatch.setattr(workflow, "evaluate_scenario", interrupted)
    with pytest.raises(ValueError, match="interruption"):
        run_evaluation(root)
    assert len(list((root / "runs").iterdir())) == 2
    assert ledger_for(root).events()[-1]["event"] == "failed"
    resumed = []

    def tracked(*args):
        resumed.append(args[-1]["scenario_id"])
        return original(*args)

    monkeypatch.setattr(workflow, "evaluate_scenario", tracked)
    result = run_evaluation(root)
    assert len(result["scenarios"]) == 8 and len(resumed) == 6
    assert not set(resumed).intersection(calls[:2])
    with pytest.raises(ValueError, match="reason"):
        ledger_for(root).require_new_reason(None)
    ledger_for(root).require_new_reason("Independent archival recovery")


def test_full_matrix_exact_replay_and_relocated_snapshot(tmp_path):
    data, source, config = source_fixture(tmp_path)
    root = tmp_path / "final"
    protocol = prepare_protocol(data, source, config, root)
    before = {row["model"]: file_hash(root / row["model"]) for row in protocol["models"]}
    result = run_evaluation(root)
    assert len(protocol["models"]) == 10 and len(result["scenarios"]) == 60
    assert sum(row["kind"] == "deterministic" for row in result["scenarios"]) == 15
    assert sum(row["kind"] == "random" for row in result["scenarios"]) == 15
    assert sum(row["kind"] == "rl" for row in result["scenarios"]) == 30
    relocated = tmp_path / "relocated.parquet"
    shutil.copy2(data, relocated)
    data.unlink()
    assert validate_protocol(root, relocated)["input_file"] == str(relocated)
    replay = verify_evaluation(root, relocated)
    assert (replay / "verification.json").is_file()
    assert before == {row["model"]: file_hash(root / row["model"]) for row in protocol["models"]}
    # Same frozen model load preserves Q and visits; no unobserved state fitting.
    for row in protocol["models"]:
        with np.load(root / row["model"]) as archive:
            assert np.isfinite(archive["q"]).all() and (archive["visits"] >= 0).all()
    assert run_evaluation(root, relocated) == result


def test_prepare_run_verify_report_through_cli(tmp_path):
    data, source, config = source_fixture(tmp_path)
    root = tmp_path / "final"
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        f'source_run = "{source}"\ntest_start = "{config.test_start}"\ntest_end = "{config.test_end}"\nseeds = [42]\ncosts_bps = [10]\n'
    )
    base = [sys.executable, "-m", "indexpilot_us100.evaluation.final.cli"]
    commands = [
        [
            "prepare",
            "--data",
            str(data),
            "--source-run",
            str(source),
            "--config",
            str(config_path),
            "--output-dir",
            str(root),
        ],
        ["run", "--protocol-dir", str(root)],
        ["verify", "--protocol-dir", str(root)],
        ["report", "--protocol-dir", str(root)],
    ]
    for command in commands:
        subprocess.run(base + command, check=True, capture_output=True, text=True, timeout=60)
    assert (root / "report.md").is_file()
    events = ledger_for(root).events()
    assert events[0]["event"] == "prepared" and events[-1]["event"] == "verified"
    assert len(json.loads((root / "primary_summary.json").read_text())) == 8
