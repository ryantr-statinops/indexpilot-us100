"""Fixed causal state bins; no data-dependent fitting."""

import numpy as np

from indexpilot_us100.portfolio import Observation

ACTIONS = (-1.0, -0.5, 0.0, 0.5, 1.0)
FEATURE_NAMES = ("return_1", "return_5", "return_20", "volatility", "exposure", "drawdown")
BIN_EDGES = (
    (-0.02, 0.0, 0.02),
    (-0.05, 0.0, 0.05),
    (-0.1, 0.0, 0.1),
    (0.01, 0.02, 0.04),
    (-0.75, -0.25, 0.25, 0.75),
    (0.1, 0.25),
)
STATE_SHAPE = tuple(len(edges) + 1 for edges in BIN_EDGES)
STATE_COUNT = int(np.prod(STATE_SHAPE))


def observation_vector(observation: Observation) -> np.ndarray:
    features = observation.features
    vector = np.array(
        [
            features.return_1,
            features.return_5,
            features.return_20,
            features.volatility,
            observation.exposure,
            observation.drawdown,
        ],
        dtype=np.float64,
    )
    if not np.all(np.isfinite(vector)) or vector[3] < 0 or not 0 <= vector[5] < 1:
        raise ValueError("State features must be finite; volatility>=0 and live drawdown in [0,1)")
    return vector


def encode_state(observation: Observation) -> int:
    vector = observation_vector(observation)
    bins = tuple(
        int(np.searchsorted(edges, value, side="right")) for edges, value in zip(BIN_EDGES, vector)
    )
    return int(np.ravel_multi_index(bins, STATE_SHAPE))
