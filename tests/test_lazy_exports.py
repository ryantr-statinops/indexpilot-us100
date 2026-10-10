"""Lazy package exports preserve implementation identity and defer loading."""

from types import SimpleNamespace

from indexpilot_us100 import _exports


def test_declared_export_is_loaded_once_and_cached(monkeypatch):
    value = object()
    calls = []

    def load(module_name, package):
        calls.append((module_name, package))
        return SimpleNamespace(Thing=value)

    monkeypatch.setattr(_exports, "import_module", load)
    namespace = {}
    mapping = {"Thing": (".core", "Thing")}
    assert _exports.resolve_export("example", "Thing", mapping, namespace) is value
    assert namespace["Thing"] is value
    assert _exports.resolve_export("example", "Thing", mapping, namespace) is value
    assert calls == [(".core", "example")]


def test_unknown_export_raises_attribute_error_without_importing(monkeypatch):
    import pytest

    def fail_import(*args):
        pytest.fail("unknown exports must not import implementation modules")

    monkeypatch.setattr(_exports, "import_module", fail_import)
    namespace = {}
    with pytest.raises(AttributeError, match="'example'.*'Missing'"):
        _exports.resolve_export("example", "Missing", {"Thing": (".core", "Thing")}, namespace)
    assert namespace == {}


def test_failed_export_load_is_not_cached(monkeypatch):
    import pytest

    calls = []

    def fail_import(*args):
        calls.append(args)
        raise ImportError("implementation unavailable")

    monkeypatch.setattr(_exports, "import_module", fail_import)
    namespace = {}
    mapping = {"Thing": (".core", "Thing")}
    with pytest.raises(ImportError, match="implementation unavailable"):
        _exports.resolve_export("example", "Thing", mapping, namespace)
    assert namespace == {}
    assert calls == [(".core", "example")]


def test_public_facades_resolve_declared_names_to_original_objects():
    from importlib import import_module

    packages = {
        "indexpilot_us100.metrics": {
            "Metric": ".core",
            "MetricsReport": ".core",
            "compute_metrics": ".core",
            "drawdown_curve": ".core",
            "sharpe_ratio": ".core",
            "compound_growth": ".core",
            "profit_factor": ".core",
            "calmar_ratio": ".core",
        },
        "indexpilot_us100.portfolio": {
            "Account": ".account",
            "Execution": ".account",
            "TargetExposure": ".account",
            "HoldPosition": ".account",
            "SimulationConfig": ".config",
            "MarketData": ".market",
            "MarketFeatures": ".market",
            "Observation": ".simulator",
            "Policy": ".simulator",
            "SimulationResult": ".simulator",
            "CashPolicy": ".baselines",
            "BuyHoldPolicy": ".baselines",
            "FixedExposurePolicy": ".baselines",
            "SMAPolicy": ".baselines",
            "RandomPolicy": ".baselines",
            "rebalance": ".account",
            "run_episode": ".simulator",
            "baseline_policies": ".baselines",
            "load_market_data": ".market",
            "decision_indices": ".market",
            "market_features": ".market",
        },
        "indexpilot_us100.agents": {
            "LearningConfig": ".config",
            "QLearningAgent": ".qlearning",
            "Experiment": ".training",
            "load_learning_config": ".config",
            "train_agent": ".training",
            "run_experiments": ".training",
            "chronological_segments": ".training",
            "ACTIONS": ".state",
            "BIN_EDGES": ".state",
            "FEATURE_NAMES": ".state",
            "STATE_SHAPE": ".state",
            "STATE_COUNT": ".state",
            "observation_vector": ".state",
            "encode_state": ".state",
        },
        "indexpilot_us100.environment": {
            name: ".trading" for name in ("TradingEnvironment", "Trajectory", "Transition")
        },
        "indexpilot_us100.data": {
            "download_daily": ".download",
            "normalize_download": ".download",
            "process_source_table": ".download",
            "process_raw_csv": ".download",
            "summarize": ".inspect",
        },
        "indexpilot_us100.evaluation": {
            "export_results": ".export",
            "export_learning": ".learning_export",
            "load_chart_series": ".chart",
            "create_chart": ".chart",
            "file_hash": ".export",
            "git_revision": ".export",
            "write_json": ".export",
            "write_json_atomic": ".export",
            "trajectory_records": ".learning_export",
        },
        "indexpilot_us100.evaluation.final": {
            "EvaluationConfig": ".config",
            "ExperimentLedger": ".history",
            "prepare_protocol": ".protocol",
            "validate_protocol": ".protocol",
            "run_evaluation": ".workflow",
            "verify_evaluation": ".workflow",
            "check_complete": ".completion",
            "frozen_path": ".protocol",
            "ReportContext": ".report",
            "load_report_context": ".report",
            "render_report": ".report",
            "generate_report": ".report",
            **{
                name: ".types"
                for name in (
                    "Scenario",
                    "ModelInventory",
                    "Coverage",
                    "YearCoverage",
                    "DecisionRecord",
                    "EnvironmentRecord",
                    "ScoreRow",
                    "FrozenProtocol",
                    "RunManifest",
                )
            },
        },
    }
    for package_name, expected_modules in packages.items():
        package = import_module(package_name)
        assert set(package.__all__) == set(expected_modules)
        assert set(package.__all__) <= set(dir(package))
        for name, relative_module in expected_modules.items():
            expected = getattr(import_module(relative_module, package_name), name)
            assert getattr(package, name) is expected
            assert getattr(package, name) is expected


def test_package_facades_import_in_both_cyclic_orders():
    import subprocess
    import sys

    scripts = (
        """
from indexpilot_us100.agents import QLearningAgent
from indexpilot_us100.environment import TradingEnvironment
from indexpilot_us100.agents import QLearningAgent as CachedAgent
assert CachedAgent is QLearningAgent
assert TradingEnvironment.__module__ == 'indexpilot_us100.environment.trading'
""",
        """
from indexpilot_us100.environment import TradingEnvironment
from indexpilot_us100.agents import QLearningAgent
assert TradingEnvironment.__module__ == 'indexpilot_us100.environment.trading'
assert QLearningAgent.__module__ == 'indexpilot_us100.agents.qlearning'
""",
        """
from indexpilot_us100.evaluation.final import RunManifest, check_complete
from indexpilot_us100.evaluation import file_hash
assert RunManifest is not None and callable(check_complete) and callable(file_hash)
""",
        """
from indexpilot_us100.evaluation import file_hash
from indexpilot_us100.evaluation.final import RunManifest, check_complete
assert RunManifest is not None and callable(check_complete) and callable(file_hash)
""",
    )
    for script in scripts:
        result = subprocess.run(
            [sys.executable, "-c", script], capture_output=True, text=True, check=False
        )
        assert result.returncode == 0, result.stderr


def test_importing_packages_does_not_load_optional_dependencies():
    import subprocess
    import sys

    script = """
import builtins
real_import = builtins.__import__
def guarded(name, *args, **kwargs):
    if name.split('.')[0] in {'numpy', 'polars', 'yfinance', 'finplot', 'PyQt6'}:
        raise AssertionError(f'package import eagerly loaded {name}')
    return real_import(name, *args, **kwargs)
builtins.__import__ = guarded
import indexpilot_us100.metrics
import indexpilot_us100.portfolio
import indexpilot_us100.agents
import indexpilot_us100.environment
import indexpilot_us100.data
import indexpilot_us100.evaluation
import indexpilot_us100.evaluation.final
"""
    result = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stderr


def test_chart_facade_defers_finplot_until_chart_creation():
    import subprocess
    import sys

    script = """
import sys
from indexpilot_us100.evaluation import create_chart
assert 'finplot' not in sys.modules
"""
    result = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stderr
