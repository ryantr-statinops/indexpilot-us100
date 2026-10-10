"""Public API for the data package."""

from typing import TYPE_CHECKING, Any

from indexpilot_us100._exports import resolve_export as _resolve_export

if TYPE_CHECKING:
    from .download import (
        download_daily,
        normalize_download,
        process_raw_csv,
        process_source_table,
    )
    from .inspect import (
        summarize,
    )

__all__ = [
    "download_daily",
    "normalize_download",
    "process_source_table",
    "process_raw_csv",
    "summarize",
]

_EXPORTS = {
    "download_daily": (".download", "download_daily"),
    "normalize_download": (".download", "normalize_download"),
    "process_source_table": (".download", "process_source_table"),
    "process_raw_csv": (".download", "process_raw_csv"),
    "summarize": (".inspect", "summarize"),
}


def __getattr__(name: str) -> Any:
    return _resolve_export(__name__, name, _EXPORTS, globals())


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
