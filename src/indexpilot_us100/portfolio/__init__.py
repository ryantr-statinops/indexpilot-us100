"""Public API for the portfolio package."""

from typing import TYPE_CHECKING, Any

from indexpilot_us100._exports import resolve_export as _resolve_export

if TYPE_CHECKING:
    from .account import (
        Account,
        Execution,
        HoldPosition,
        TargetExposure,
        rebalance,
    )
    from .baselines import (
        BuyHoldPolicy,
        CashPolicy,
        FixedExposurePolicy,
        RandomPolicy,
        SMAPolicy,
        baseline_policies,
    )
    from .config import (
        SimulationConfig,
    )
    from .market import (
        MarketData,
        MarketFeatures,
        decision_indices,
        load_market_data,
        market_features,
    )
    from .simulator import (
        Observation,
        Policy,
        SimulationResult,
        run_episode,
    )

__all__ = [
    "Account",
    "Execution",
    "TargetExposure",
    "HoldPosition",
    "SimulationConfig",
    "MarketData",
    "MarketFeatures",
    "Observation",
    "Policy",
    "SimulationResult",
    "CashPolicy",
    "BuyHoldPolicy",
    "FixedExposurePolicy",
    "SMAPolicy",
    "RandomPolicy",
    "rebalance",
    "run_episode",
    "baseline_policies",
    "load_market_data",
    "decision_indices",
    "market_features",
]

_EXPORTS = {
    "Account": (".account", "Account"),
    "Execution": (".account", "Execution"),
    "TargetExposure": (".account", "TargetExposure"),
    "HoldPosition": (".account", "HoldPosition"),
    "SimulationConfig": (".config", "SimulationConfig"),
    "MarketData": (".market", "MarketData"),
    "MarketFeatures": (".market", "MarketFeatures"),
    "Observation": (".simulator", "Observation"),
    "Policy": (".simulator", "Policy"),
    "SimulationResult": (".simulator", "SimulationResult"),
    "CashPolicy": (".baselines", "CashPolicy"),
    "BuyHoldPolicy": (".baselines", "BuyHoldPolicy"),
    "FixedExposurePolicy": (".baselines", "FixedExposurePolicy"),
    "SMAPolicy": (".baselines", "SMAPolicy"),
    "RandomPolicy": (".baselines", "RandomPolicy"),
    "rebalance": (".account", "rebalance"),
    "run_episode": (".simulator", "run_episode"),
    "baseline_policies": (".baselines", "baseline_policies"),
    "load_market_data": (".market", "load_market_data"),
    "decision_indices": (".market", "decision_indices"),
    "market_features": (".market", "market_features"),
}


def __getattr__(name: str) -> Any:
    return _resolve_export(__name__, name, _EXPORTS, globals())


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
