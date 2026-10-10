"""Public metric types and portfolio performance calculations."""

from typing import TYPE_CHECKING, Any

from indexpilot_us100._exports import resolve_export as _resolve_export

if TYPE_CHECKING:
    from .core import (
        Metric,
        MetricsReport,
        calmar_ratio,
        compound_growth,
        compute_metrics,
        drawdown_curve,
        profit_factor,
        sharpe_ratio,
    )

__all__ = [
    "Metric",
    "MetricsReport",
    "compute_metrics",
    "drawdown_curve",
    "sharpe_ratio",
    "compound_growth",
    "profit_factor",
    "calmar_ratio",
]

_EXPORTS = {name: (".core", name) for name in __all__}


def __getattr__(name: str) -> Any:
    return _resolve_export(__name__, name, _EXPORTS, globals())


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
