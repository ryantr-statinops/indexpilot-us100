"""Validate Stage 3 provenance before preparing any final models."""

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from indexpilot_us100.agents.config import LearningConfig
from indexpilot_us100.agents.qlearning import QLearningAgent
from indexpilot_us100.agents.state import ACTIONS, BIN_EDGES, FEATURE_NAMES, STATE_COUNT
from indexpilot_us100.portfolio.config import SimulationConfig

from ..export import file_hash
from .config import EvaluationConfig


@dataclass
class ValidatedSource:
    root: Path
    manifest: dict
    simulation: SimulationConfig
    learning: LearningConfig
    models: dict[float, Path]


def validate_source(
    input_path: str | Path, source_run: str | Path, config: EvaluationConfig
) -> ValidatedSource:
    root = Path(source_run).resolve()
    manifest = json.loads((root / "run_manifest.json").read_text())
    if manifest.get("artifact_type") != "indexpilot-stage-3" or manifest.get("schema_version") != 1:
        raise ValueError("Expected a Stage 3 manifest version1")
    if manifest["input_sha256"] != file_hash(Path(input_path)):
        raise ValueError("Data hash differs from Stage 3 snapshot")
    selection = json.loads((root / "selection.json").read_text())
    if selection.get("status") != "selected" or selection.get("test_evaluated") is not False:
        raise ValueError("Source selection must precede reserved test evaluation")
    if selection != manifest["selection"] or selection["selected_lambda"] != config.primary_lambda:
        raise ValueError("Selection does not match frozen primary lambda")
    expected = dict(
        features=list(FEATURE_NAMES),
        bin_edges=[list(edges) for edges in BIN_EDGES],
        state_count=STATE_COUNT,
        actions=list(ACTIONS),
    )
    if manifest["state_definition"] != expected:
        raise ValueError("Source state definitions are incompatible")
    simulation = SimulationConfig(**manifest["simulation_config"])
    values = dict(manifest["learning_config"])
    values["lambdas"] = tuple(values["lambdas"])
    learning = LearningConfig(**values)
    if (
        simulation.seed != config.primary_seed
        or simulation.cost_bps != config.primary_cost_bps
        or learning.test_start != config.test_start
    ):
        raise ValueError("Source seed/cost/test boundary conflicts with evaluation protocol")
    if date.fromisoformat(config.test_start) <= date.fromisoformat(learning.validation_end):
        raise ValueError("Test overlaps validation")
    index = selection["selected_index"]
    if (
        type(index) is not int
        or not 0 <= index < len(manifest["experiments"])
        or manifest["experiments"][index]["risk_lambda"] != config.primary_lambda
    ):
        raise ValueError("Invalid selected model index")
    models = {}
    for risk_lambda in (config.reference_lambda, config.primary_lambda):
        matches = [
            entry for entry in manifest["experiments"] if entry["risk_lambda"] == risk_lambda
        ]
        if len(matches) != 1 or risk_lambda not in learning.lambdas:
            raise ValueError("Required source lambda checkpoint missing")
        directory = matches[0]["model_directory"]
        if not directory or not all(char.isalnum() or char in "_-" for char in directory):
            raise ValueError("Unsafe source model directory")
        path = root / directory / "model.npz"
        QLearningAgent.load(path, learning)
        models[risk_lambda] = path
    return ValidatedSource(root, manifest, simulation, learning, models)
