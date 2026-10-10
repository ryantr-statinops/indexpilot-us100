"""Public API for the agents package."""

from typing import TYPE_CHECKING, Any

from indexpilot_us100._exports import resolve_export as _resolve_export

if TYPE_CHECKING:
    from .config import (
        LearningConfig,
        load_learning_config,
    )
    from .qlearning import (
        QLearningAgent,
    )
    from .state import (
        ACTIONS,
        BIN_EDGES,
        FEATURE_NAMES,
        STATE_COUNT,
        STATE_SHAPE,
        encode_state,
        observation_vector,
    )
    from .training import (
        Experiment,
        chronological_segments,
        run_experiments,
        train_agent,
    )

__all__ = [
    "LearningConfig",
    "QLearningAgent",
    "Experiment",
    "load_learning_config",
    "train_agent",
    "run_experiments",
    "chronological_segments",
    "ACTIONS",
    "BIN_EDGES",
    "FEATURE_NAMES",
    "STATE_SHAPE",
    "STATE_COUNT",
    "observation_vector",
    "encode_state",
]

_EXPORTS = {
    "LearningConfig": (".config", "LearningConfig"),
    "QLearningAgent": (".qlearning", "QLearningAgent"),
    "Experiment": (".training", "Experiment"),
    "load_learning_config": (".config", "load_learning_config"),
    "train_agent": (".training", "train_agent"),
    "run_experiments": (".training", "run_experiments"),
    "chronological_segments": (".training", "chronological_segments"),
    "ACTIONS": (".state", "ACTIONS"),
    "BIN_EDGES": (".state", "BIN_EDGES"),
    "FEATURE_NAMES": (".state", "FEATURE_NAMES"),
    "STATE_SHAPE": (".state", "STATE_SHAPE"),
    "STATE_COUNT": (".state", "STATE_COUNT"),
    "observation_vector": (".state", "observation_vector"),
    "encode_state": (".state", "encode_state"),
}


def __getattr__(name: str) -> Any:
    return _resolve_export(__name__, name, _EXPORTS, globals())


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
