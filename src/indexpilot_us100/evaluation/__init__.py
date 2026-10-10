"""Public API for the evaluation package."""

from typing import TYPE_CHECKING, Any

from indexpilot_us100._exports import resolve_export as _resolve_export

if TYPE_CHECKING:
    from .chart import (
        create_chart,
        load_chart_series,
    )
    from .export import (
        export_results,
        file_hash,
        git_revision,
        write_json,
        write_json_atomic,
    )
    from .learning_export import (
        export_learning,
        trajectory_records,
    )

__all__ = [
    "export_results",
    "export_learning",
    "load_chart_series",
    "create_chart",
    "file_hash",
    "git_revision",
    "write_json",
    "write_json_atomic",
    "trajectory_records",
]

_EXPORTS = {
    "export_results": (".export", "export_results"),
    "export_learning": (".learning_export", "export_learning"),
    "load_chart_series": (".chart", "load_chart_series"),
    "create_chart": (".chart", "create_chart"),
    "file_hash": (".export", "file_hash"),
    "git_revision": (".export", "git_revision"),
    "write_json": (".export", "write_json"),
    "write_json_atomic": (".export", "write_json_atomic"),
    "trajectory_records": (".learning_export", "trajectory_records"),
}


def __getattr__(name: str) -> Any:
    return _resolve_export(__name__, name, _EXPORTS, globals())


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
