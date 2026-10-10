"""Public API for the environment package."""

from typing import TYPE_CHECKING, Any

from indexpilot_us100._exports import resolve_export as _resolve_export

if TYPE_CHECKING:
    from .trading import (
        TradingEnvironment,
        Trajectory,
        Transition,
    )

__all__ = [
    "TradingEnvironment",
    "Trajectory",
    "Transition",
]

_EXPORTS = {
    "TradingEnvironment": (".trading", "TradingEnvironment"),
    "Trajectory": (".trading", "Trajectory"),
    "Transition": (".trading", "Transition"),
}


def __getattr__(name: str) -> Any:
    return _resolve_export(__name__, name, _EXPORTS, globals())


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
