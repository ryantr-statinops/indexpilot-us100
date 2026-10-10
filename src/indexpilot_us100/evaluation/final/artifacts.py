"""Atomic scenario artifacts and integrity-checked resumable results."""

import json
import shutil
import tempfile
from pathlib import Path
from typing import Any

import polars as pl

from indexpilot_us100.metrics import compute_metrics

from ..export import export_results, file_hash, write_json
from ..learning_export import trajectory_records
from .diagnostics import policy_diagnostics
from .protocol import frozen_path
from .runner import EvaluatedRun
from .types import FrozenProtocol, ScoreRow

TRANSITION_SCHEMA = {
    "state": pl.Int64,
    "action": pl.Int64,
    "reward": pl.Float64,
    "next_state": pl.Int64,
    "terminated": pl.Boolean,
    "date": pl.Date,
    "end_date": pl.Date,
}


def artifact_hashes(root) -> dict[str, str]:
    root = Path(root)
    return {
        str(path.relative_to(root)): file_hash(path)
        for path in sorted(root.rglob("*"))
        if path.is_file() and path.name != "completion.json"
    }


def check_run(directory, protocol_id: str) -> ScoreRow:
    root = Path(directory)
    marker = json.loads((root / "completion.json").read_text())
    if marker["protocol_id"] != protocol_id or marker["hashes"] != artifact_hashes(root):
        raise ValueError("Scenario artifact integrity failed")
    return json.loads((root / "score.json").read_text())


def score_row(run: EvaluatedRun, protocol: FrozenProtocol) -> ScoreRow:
    row = compute_metrics(run.result).row()
    config = protocol["evaluation_config"]
    scenario = run.scenario
    coverage = protocol["intended_coverage"]
    role = (
        ("primary" if scenario["risk_lambda"] == config["primary_lambda"] else "reference")
        if scenario["kind"] == "rl"
        else "baseline"
    )
    return {
        **row,
        **scenario,
        "role": role,
        "intended_start_date": coverage["start_date"],
        "intended_end_date": coverage["end_date"],
        "intended_interval_count": coverage["interval_count"],
    }


def store_run(root, protocol: FrozenProtocol, run: EvaluatedRun) -> ScoreRow:
    runs = Path(root) / "runs"
    runs.mkdir(exist_ok=True)
    target = frozen_path(root, "runs/" + run.scenario["scenario_id"])
    if target.exists():
        return check_run(target, protocol["protocol_id"])
    with tempfile.TemporaryDirectory(prefix=".scenario-", dir=runs) as temporary:
        directory = Path(temporary)
        export_results([run.result], protocol["input_file"], directory / "accounting")
        if run.trajectory is not None:
            pl.DataFrame(
                trajectory_records(run.trajectory), schema=TRANSITION_SCHEMA
            ).write_parquet(directory / "transitions.parquet")
        pl.DataFrame(
            run.decisions,
            schema={
                "date": pl.Date,
                "state": pl.Int64,
                "target": pl.Float64,
                "exposure_before": pl.Float64,
                "holdings_before": pl.Float64,
                "equity_before": pl.Float64,
            },
        ).write_parquet(directory / "decisions.parquet")
        diagnostics = policy_diagnostics(run)
        write_json(directory / "diagnostics.json", diagnostics)
        row = {
            **score_row(run, protocol),
            **{
                key: diagnostics[key]
                for key in (
                    "flat_decision_fraction",
                    "active_intervals",
                    "mean_gross_exposure",
                    "max_gross_exposure",
                    "unseen_state_fraction",
                )
            },
        }
        write_json(directory / "score.json", row)
        write_json(
            directory / "scenario.json",
            dict(
                protocol_id=protocol["protocol_id"],
                scenario=run.scenario,
                input_sha256=protocol["input_sha256"],
            ),
        )
        write_json(
            directory / "completion.json",
            dict(protocol_id=protocol["protocol_id"], hashes=artifact_hashes(directory)),
        )
        shutil.move(str(directory), str(target))
    return row


def write_table(root, name: str, rows: list[dict[str, Any]]) -> None:
    root = Path(root)
    pl.DataFrame(rows, infer_schema_length=None).write_csv(root / f"{name}.csv")
    write_json(root / f"{name}.json", rows)
