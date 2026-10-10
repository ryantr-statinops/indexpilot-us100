"""Integrity checks for completed evaluation artifacts, shared by readers and runners."""

import json
from pathlib import Path

from indexpilot_us100.evaluation import file_hash

from .artifacts import check_run
from .matrix import scenarios
from .protocol import frozen_path
from .types import FrozenProtocol, RunManifest, ScoreRow

SUMMARY_FILES = (
    "primary_summary.csv",
    "primary_summary.json",
    "scenario_summary.csv",
    "scenario_summary.json",
    "seed_summary.csv",
    "seed_summary.json",
    "paired_comparison.csv",
    "paired_comparison.json",
    "yearly_summary.csv",
    "yearly_summary.json",
    "diagnostics.json",
)


def checked_scores(root, protocol: FrozenProtocol) -> list[ScoreRow]:
    return [
        check_run(frozen_path(root, "runs/" + row["scenario_id"]), protocol["protocol_id"])
        for row in scenarios(protocol)
    ]


def check_complete(root, protocol: FrozenProtocol) -> RunManifest:
    root = Path(root)
    manifest = json.loads((root / "run_manifest.json").read_text())
    if (
        manifest.get("protocol_id") != protocol["protocol_id"]
        or manifest.get("artifact_type") != "indexpilot-stage-4"
    ):
        raise ValueError("Completed run protocol mismatch")
    actual = {name: file_hash(root / name) for name in SUMMARY_FILES}
    if manifest.get("summary_hashes") != actual:
        raise ValueError("Completed summary integrity failed")
    scores = checked_scores(root, protocol)
    if manifest.get("scenarios") != scores:
        raise ValueError("Completed scenario inventory mismatch")
    return manifest
