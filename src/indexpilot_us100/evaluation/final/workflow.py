"""Frozen evaluation, resumable scenario execution and independent replay."""

from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import polars as pl
from indexpilot_us100.portfolio.market import load_market_data
from indexpilot_us100.portfolio.config import SimulationConfig
from ..export import file_hash, write_json, write_json_atomic, git_revision
from .aggregation import aggregate_seed_results
from .artifacts import check_run, store_run, write_table
from .comparison import paired_comparison
from .completion import SUMMARY_FILES as SUMMARY_FILES, checked_scores as checked_scores, check_complete as check_complete
from .config import EvaluationConfig
from .history import ExperimentLedger, run_lock
from .matrix import scenarios, evaluate_scenario
from .protocol import validate_protocol, environment, frozen_path
from .windows import build_test_segment
from .yearly import yearly_summary, expected_yearly_coverage
from .types import FrozenProtocol, RunManifest, ScoreRow, YearCoverage

def evaluation_config(protocol: FrozenProtocol) -> EvaluationConfig:
    values = dict(protocol["evaluation_config"])
    values["seeds"] = tuple(values["seeds"])
    values["costs_bps"] = tuple(values["costs_bps"])
    return EvaluationConfig(**values)


def ledger_for(root) -> ExperimentLedger:
    return ExperimentLedger(Path(root).parent / "experiment-ledger.jsonl")


def _read_run_artifacts(directory: Path, baseline: str):
    diagnostics = json.loads((directory / "diagnostics.json").read_text())
    accounting = directory / "accounting" / baseline
    intervals = pl.read_parquet(accounting / "intervals.parquet").to_dicts()
    decisions = pl.read_parquet(directory / "decisions.parquet").to_dicts()
    events = [
        event
        for event in pl.read_parquet(accounting / "ledger.parquet").to_dicts()
        if event["kind"] in ("execution", "hold")
    ]
    trades = pl.read_parquet(accounting / "trades.parquet").to_dicts()
    return diagnostics, intervals, decisions, events, trades


def summarize(
    root, protocol: FrozenProtocol, scores: list[ScoreRow], expected_years: dict[int, YearCoverage]
) -> RunManifest:
    root = Path(root)
    config = protocol["evaluation_config"]
    primary = [
        row
        for row in scores
        if row["seed"] == config["primary_seed"] and row["cost_bps"] == config["primary_cost_bps"]
    ]
    write_table(root, "scenario_summary", scores)
    write_table(root, "primary_summary", primary)
    write_table(root, "seed_summary", aggregate_seed_results(scores))
    write_table(
        root,
        "paired_comparison",
        paired_comparison(scores, config["primary_lambda"], config["reference_lambda"]),
    )
    diagnostics = {}
    years = []
    for row in scores:
        directory = frozen_path(root, "runs/" + row["scenario_id"])
        diagnostic, intervals, decisions, events, trades = _read_run_artifacts(directory, row["baseline"])
        diagnostics[row["scenario_id"]] = diagnostic
        years += yearly_summary(row, intervals, decisions, events, trades, protocol, expected_years)
    write_table(root, "yearly_summary", years)
    write_json(root / "diagnostics.json", diagnostics)
    manifest = dict(
        artifact_type="indexpilot-stage-4",
        schema_version=1,
        protocol_id=protocol["protocol_id"],
        created_at=datetime.now(timezone.utc).isoformat(),
        git_revision=git_revision(),
        environment=environment(),
        input_sha256=protocol["input_sha256"],
        effective_input_file=protocol["input_file"],
        intended_coverage=protocol["intended_coverage"],
        scenarios=scores,
        summary_hashes={name: file_hash(root / name) for name in SUMMARY_FILES},
    )
    write_json_atomic(root / "run_manifest.json", manifest)
    return manifest


def _test_segment(protocol: FrozenProtocol):
    return build_test_segment(
        load_market_data(protocol["input_file"]),
        evaluation_config(protocol),
        SimulationConfig(**protocol["simulation_config"]),
    )


def _run_or_reuse_scenario(root: Path, protocol: FrozenProtocol, segment, scenario, history: ExperimentLedger) -> ScoreRow:
    directory = frozen_path(root, "runs/" + scenario["scenario_id"])
    if directory.exists():
        score = check_run(directory, protocol["protocol_id"])
    else:
        score = store_run(
            root, protocol, evaluate_scenario(root, protocol, segment, scenario)
        )
        history.append(
            "scenario_completed",
            protocol["protocol_id"],
            scenario_id=scenario["scenario_id"],
            status=score["status"],
        )
    return score


def _recover_completed_event(history: ExperimentLedger, protocol: FrozenProtocol, manifest: RunManifest) -> None:
    if not any(
        event["event"] == "completed" and event["protocol_id"] == protocol["protocol_id"]
        for event in history.events()
    ):
        history.append(
            "completed",
            protocol["protocol_id"],
            recovered=True,
            scenarios=[row["scenario_id"] for row in manifest["scenarios"]],
            summary_hashes=manifest["summary_hashes"],
        )


def _execute_scenarios(root: Path, protocol: FrozenProtocol, segment, output_root: Path, completed: list[str], progress=None, history: ExperimentLedger | None = None) -> list[ScoreRow]:
    scores = []
    for scenario in scenarios(protocol):
        if history is not None:
            score = _run_or_reuse_scenario(root, protocol, segment, scenario, history)
        else:
            score = store_run(output_root, protocol, evaluate_scenario(root, protocol, segment, scenario))
        scores.append(score)
        completed.append(scenario["scenario_id"])
        if progress:
            progress(scenario["scenario_id"])
    return scores


def run_evaluation(protocol_dir, input_path=None, progress=None) -> RunManifest:
    root = Path(protocol_dir)
    protocol = validate_protocol(root, input_path)
    history = ledger_for(root)
    with run_lock(root):
        if (root / "run_manifest.json").exists():
            manifest = check_complete(root, protocol)
            _recover_completed_event(history, protocol, manifest)
            return manifest
        completed = []
        history.append(
            "started",
            protocol["protocol_id"],
            input_sha256=protocol["input_sha256"],
            model_hashes=[row["sha256"] for row in protocol["models"]],
        )
        try:
            segment = _test_segment(protocol)
            scores = _execute_scenarios(root, protocol, segment, root, completed, progress, history)
            validate_protocol(root, input_path)
            manifest = summarize(
                root,
                protocol,
                scores,
                expected_yearly_coverage(
                    segment, SimulationConfig(**protocol["simulation_config"])
                ),
            )
            check_complete(root, protocol)
            history.append(
                "completed",
                protocol["protocol_id"],
                scenarios=completed,
                summary_hashes=manifest["summary_hashes"],
            )
            return manifest
        except Exception as error:
            history.append(
                "failed", protocol["protocol_id"], completed_scenarios=completed, error=str(error)
            )
            raise


def compare_replay(original, replay, protocol: FrozenProtocol) -> None:
    original = Path(original)
    replay = Path(replay)
    for name in SUMMARY_FILES:
        if file_hash(original / name) != file_hash(replay / name):
            raise ValueError("Replay summary differs: " + name)
    for scenario in scenarios(protocol):
        left = frozen_path(original, "runs/" + scenario["scenario_id"])
        right = frozen_path(replay, "runs/" + scenario["scenario_id"])
        for path in left.rglob("*"):
            if not path.is_file() or path.name in ("completion.json", "run_manifest.json"):
                continue
            counterpart = right / path.relative_to(left)
            if path.suffix == ".parquet":
                equal = pl.read_parquet(path).equals(pl.read_parquet(counterpart))
            else:
                equal = path.read_bytes() == counterpart.read_bytes()
            if not equal:
                raise ValueError("Replay artifact differs: " + str(path.relative_to(original)))


def verify_evaluation(protocol_dir, input_path=None, progress=None) -> Path:
    root = Path(protocol_dir)
    protocol = validate_protocol(root, input_path)
    with run_lock(root):
        check_complete(root, protocol)
        replay = Path(tempfile.mkdtemp(prefix="verification-", dir=root))
        try:
            segment = _test_segment(protocol)
            scores = _execute_scenarios(root, protocol, segment, replay, [], progress)
            summarize(
                replay,
                protocol,
                scores,
                expected_yearly_coverage(
                    segment, SimulationConfig(**protocol["simulation_config"])
                ),
            )
            compare_replay(root, replay, protocol)
            validate_protocol(root, input_path)
            write_json(
                replay / "verification.json",
                dict(
                    protocol_id=protocol["protocol_id"],
                    status="verified",
                    scenario_count=len(scores),
                ),
            )
            ledger_for(root).append(
                "verified",
                protocol["protocol_id"],
                replay_directory=str(replay),
                scenario_count=len(scores),
            )
            return replay
        except Exception as error:
            ledger_for(root).append(
                "verification_failed",
                protocol["protocol_id"],
                replay_directory=str(replay),
                error=str(error),
            )
            raise
