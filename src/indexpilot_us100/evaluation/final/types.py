"""Static contracts for existing evaluation dictionaries; no wire conversion."""

from datetime import date
from typing import Any, Literal, NotRequired, TypedDict

MetricStatus = Literal["finite", "undefined", "positive_infinity", "not_applicable"]
RunStatus = Literal["completed", "insolvent"]


class Scenario(TypedDict):
    kind: Literal["rl", "random", "deterministic"]
    policy: str
    seed: int
    risk_lambda: float
    cost_bps: float
    scenario_id: NotRequired[str]


class ModelInventory(TypedDict):
    seed: int
    risk_lambda: float
    model: str
    sha256: str
    training_log: str
    training_log_sha256: str
    reused_stage3: bool


class Coverage(TypedDict):
    start_date: str
    end_date: str
    interval_count: int


class YearCoverage(TypedDict):
    start_date: date
    end_date: date


class DecisionRecord(TypedDict):
    date: date
    state: int
    target: float | None
    exposure_before: float
    holdings_before: float
    equity_before: float


class EnvironmentRecord(TypedDict):
    python: str
    implementation: str
    platform: str
    packages: dict[str, str | None]


class ScoreRow(Scenario, total=False):
    baseline: str
    role: Literal["primary", "reference", "baseline"]
    status: RunStatus
    start_date: str
    end_date: str
    interval_count: int
    intended_start_date: str
    intended_end_date: str
    intended_interval_count: int
    initial_equity: float
    final_equity: float
    net_pnl: float
    net_return: float
    total_fees: float
    traded_notional: float
    normalized_turnover: float
    order_count: int
    trade_count: int
    wins: int
    losses: int
    breakeven: int
    total_reward: float
    flat_decision_fraction: float
    active_intervals: int
    mean_gross_exposure: float
    max_gross_exposure: float
    unseen_state_fraction: float | None
    sharpe: float | None
    sharpe_status: MetricStatus
    max_drawdown: float
    max_drawdown_status: MetricStatus
    cagr: float | None
    cagr_status: MetricStatus
    profit_factor: float | None
    profit_factor_status: MetricStatus
    calmar: float | None
    calmar_status: MetricStatus


class FrozenProtocol(TypedDict):
    artifact_type: str
    schema_version: int
    protocol_id: str
    created_at: str
    input_file: str
    input_sha256: str
    source_manifest_sha256: str
    source_selection_sha256: str
    evaluation_config: dict[str, Any]
    simulation_config: dict[str, Any]
    learning_config: dict[str, Any]
    state_definition: dict[str, Any]
    models: list[ModelInventory]
    intended_coverage: Coverage
    environment: EnvironmentRecord
    code_fingerprints: dict[str, str]
    lock_sha256: str
    git_revision: str | None


class RunManifest(TypedDict):
    artifact_type: str
    schema_version: int
    protocol_id: str
    created_at: str
    git_revision: str | None
    environment: EnvironmentRecord
    input_sha256: str
    effective_input_file: str
    intended_coverage: Coverage
    scenarios: list[ScoreRow]
    summary_hashes: dict[str, str]
