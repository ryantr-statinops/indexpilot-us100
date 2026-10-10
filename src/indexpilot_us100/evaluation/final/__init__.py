"""Public API for the final package."""

from typing import TYPE_CHECKING, Any

from indexpilot_us100._exports import resolve_export as _resolve_export

if TYPE_CHECKING:
    from .completion import (
        check_complete,
    )
    from .config import (
        EvaluationConfig,
    )
    from .history import (
        ExperimentLedger,
    )
    from .protocol import (
        frozen_path,
        prepare_protocol,
        validate_protocol,
    )
    from .report import (
        ReportContext,
        generate_report,
        load_report_context,
        render_report,
    )
    from .types import (
        Coverage,
        DecisionRecord,
        EnvironmentRecord,
        FrozenProtocol,
        ModelInventory,
        RunManifest,
        Scenario,
        ScoreRow,
        YearCoverage,
    )
    from .workflow import (
        run_evaluation,
        verify_evaluation,
    )

__all__ = [
    "EvaluationConfig",
    "ExperimentLedger",
    "prepare_protocol",
    "validate_protocol",
    "run_evaluation",
    "verify_evaluation",
    "check_complete",
    "frozen_path",
    "ReportContext",
    "load_report_context",
    "render_report",
    "generate_report",
    "Scenario",
    "ModelInventory",
    "Coverage",
    "YearCoverage",
    "DecisionRecord",
    "EnvironmentRecord",
    "ScoreRow",
    "FrozenProtocol",
    "RunManifest",
]

_EXPORTS = {
    "EvaluationConfig": (".config", "EvaluationConfig"),
    "ExperimentLedger": (".history", "ExperimentLedger"),
    "prepare_protocol": (".protocol", "prepare_protocol"),
    "validate_protocol": (".protocol", "validate_protocol"),
    "run_evaluation": (".workflow", "run_evaluation"),
    "verify_evaluation": (".workflow", "verify_evaluation"),
    "check_complete": (".completion", "check_complete"),
    "frozen_path": (".protocol", "frozen_path"),
    "ReportContext": (".report", "ReportContext"),
    "load_report_context": (".report", "load_report_context"),
    "render_report": (".report", "render_report"),
    "generate_report": (".report", "generate_report"),
    "Scenario": (".types", "Scenario"),
    "ModelInventory": (".types", "ModelInventory"),
    "Coverage": (".types", "Coverage"),
    "YearCoverage": (".types", "YearCoverage"),
    "DecisionRecord": (".types", "DecisionRecord"),
    "EnvironmentRecord": (".types", "EnvironmentRecord"),
    "ScoreRow": (".types", "ScoreRow"),
    "FrozenProtocol": (".types", "FrozenProtocol"),
    "RunManifest": (".types", "RunManifest"),
}


def __getattr__(name: str) -> Any:
    return _resolve_export(__name__, name, _EXPORTS, globals())


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
