"""Generate the final research report solely from checked persisted artifacts."""

import json
import shlex
from pathlib import Path
from .completion import check_complete
from dataclasses import dataclass
from typing import Any
from .types import FrozenProtocol, ScoreRow, Coverage

PERCENT_FIELDS = {
    "net_return",
    "max_drawdown",
    "cagr",
    "flat_decision_fraction",
    "unseen_state_fraction",
}


def display(row: dict[str, Any], key: str) -> str:
    value = row.get(key)
    status = row.get(key + "_status")
    if value is None:
        return "∞" if status == "positive_infinity" else "N/A"
    if isinstance(value, float):
        return f"{value * 100:.2f}%" if key in PERCENT_FIELDS else f"{value:,.4f}"
    return str(value)


def table(rows: list[dict[str, Any]], columns: list[tuple[str, str]]) -> str:
    headers = [label for _, label in columns]
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    lines += ["| " + " | ".join(display(row, key) for key, _ in columns) + " |" for row in rows]
    return """
""".join(lines)


FINANCIAL_COLUMNS = [
    ("policy", "Policy"),
    ("risk_lambda", "λ"),
    ("net_return", "Net return"),
    ("sharpe", "Sharpe"),
    ("max_drawdown", "MDD"),
    ("cagr", "CAGR"),
    ("profit_factor", "PF"),
    ("calmar", "Calmar"),
    ("trade_count", "Trades"),
    ("active_intervals", "Active"),
    ("status", "Status"),
]


@dataclass(frozen=True)
class ReportContext:
    protocol: FrozenProtocol
    primary: list[ScoreRow]
    scores: list[ScoreRow]
    seeds: list[dict[str, Any]]
    diagnostics: dict[str, dict[str, Any]]
    years: list[dict[str, Any]]
    pairs: list[dict[str, Any]]
    run_directory: Path | None = None

    @property
    def config(self) -> dict[str, Any]:
        return self.protocol["evaluation_config"]

    @property
    def instrument_label(self) -> str:
        return self.config.get("instrument_label") or "Single-asset experiment"

    @property
    def coverage(self) -> Coverage:
        return self.protocol["intended_coverage"]

    @property
    def selected(self) -> ScoreRow:
        return next(
            row
            for row in self.primary
            if row["kind"] == "rl" and row["risk_lambda"] == self.config["primary_lambda"]
        )

    @property
    def reference(self) -> ScoreRow:
        return next(
            row
            for row in self.primary
            if row["kind"] == "rl" and row["risk_lambda"] == self.config["reference_lambda"]
        )

    @property
    def active(self) -> float:
        return self.selected["active_intervals"] / self.selected["interval_count"]


def load_report_context(root: Path) -> ReportContext:
    protocol = json.loads((root / "protocol.json").read_text())
    check_complete(root, protocol)

    def read(name):
        return json.loads((root / (name + ".json")).read_text())

    return ReportContext(
        protocol,
        read("primary_summary"),
        read("scenario_summary"),
        read("seed_summary"),
        read("diagnostics"),
        read("yearly_summary"),
        read("paired_comparison"),
        root.resolve(),
    )


def research_section(context: ReportContext) -> str:
    return f"""## 1. Research question and scope

Evaluate the Q-learning policy selected by validation on a held-out test, including seed/cost variability and reproducibility. Instrument: {context.instrument_label}. This is a single-asset simulation using synthetic adjusted prices, not an actual historical broker execution."""


def data_section(context: ReportContext) -> str:
    return f"""## 2. Dữ liệu và splits

Training kết thúc {context.protocol["learning_config"]["train_end"]}; validation {context.protocol["learning_config"]["validation_start"]}–{context.protocol["learning_config"]["validation_end"]}. Test thực tế {context.coverage["start_date"]}–{context.coverage["end_date"]}, {context.coverage["interval_count"]} khoảng open-to-open. Năm cuối {context.coverage["end_date"][:4]} chưa đủ nếu snapshot kết thúc trước 31/12.

Synthetic adjusted open dùng hệ số adjusted close/raw close; holdings là đơn vị tổng hợp. Không cộng dividend/split lần nữa. Features trễ một phiên; warm-up chỉ cung cấp lịch sử, không thuộc metric coverage. Thiếu phiên không tự điền và chưa xác minh đủ lịch sàn.

Dataset SHA256: `{context.protocol["input_sha256"]}`."""


def simulation_section(context: ReportContext) -> str:
    return """## 3. Simulator và metrics

Equity = cash + holdings × price; reset flat $100.000 mỗi run. Target exposure được giải trên equity sau phí. Long/short, đơn vị lẻ, cash rate 0; chưa có borrow fee, margin call hay financing. Exposure chỉ giới hạn khi đặt target và có thể trôi. Đóng cuối có phí gộp vào interval cuối. Equity không bị chặn tại 0 khi insolvent.

Sharpe: net interval returns, ddof=1, annualization 252, risk-free 0. MDD: toàn bộ ledger kể cả sau phí. CAGR: số ngày lịch/365,25. PF: net P&L mỗi đợt vị thế, fees phân bổ reversal. Calmar = CAGR/MDD. N/A và ∞ được giữ rõ trạng thái. Reward được báo riêng, không dùng như P&L."""


def learning_section(context: ReportContext) -> str:
    return """## 4. State, actions và Q-learning

State cố định gồm return/momentum, volatility, exposure và drawdown bins; 3.840 states × 5 actions {-1,-0,5,0,0,5,1}. Reward = gross portfolio return − λ × risk − cost fraction; risk không trừ equity. Mỗi episode tạo rollout rồi cập nhật Q theo thứ tự thời gian trên transitions đã finalize. Greedy evaluation ε=0 với Q/visits chỉ đọc; không bootstrap terminal."""


def protocol_section(context: ReportContext) -> str:
    return f"""## 5. Protocol đã khóa

Protocol ID: `{context.protocol["protocol_id"]}`. Code revision khi chuẩn bị: `{context.protocol["git_revision"]}`. Source manifest SHA256: `{context.protocol["source_manifest_sha256"]}`. Primary λ={context.config["primary_lambda"]:g}, reference λ={context.config["reference_lambda"]:g}, seed {context.config["primary_seed"]}; chính luôn {context.config["primary_cost_bps"]:g} bps. Hai checkpoint seed 42 được sao chép nguyên trạng từ Stage 3. Seeds {context.config["seeds"]} dùng cùng bins/hyperparameters; seed bổ sung chỉ train trên training cũ. Không train lại primary hoặc chọn lambda/seed theo test.

Inventory {len(context.protocol["models"])} model, {len(context.scores)} scenarios. Protocol lưu hashes data/models/training logs/source/code/uv.lock và runtime. Ledger append-only ghi chuẩn bị, bắt đầu, hoàn tất, lỗi và verify."""


def primary_results_section(context: ReportContext) -> str:
    return (
        """## 6. Kết quả test chính

"""
        + table(context.primary, FINANCIAL_COLUMNS)
        + """

"""
        + table(
            context.primary,
            [
                ("policy", "Policy"),
                ("initial_equity", "Initial equity"),
                ("final_equity", "Final equity"),
                ("total_fees", "Fees"),
                ("traded_notional", "Traded notional"),
                ("normalized_turnover", "Turnover"),
                ("order_count", "Orders"),
                ("wins", "Wins"),
                ("losses", "Losses"),
                ("breakeven", "Flat P&L"),
                ("start_date", "Actual start"),
                ("end_date", "Actual end"),
                ("interval_count", "Intervals"),
            ],
        )
    )


def robustness_section(context: ReportContext) -> str:
    return (
        """## 7. Seed/cost sensitivity và mức hoạt động

"""
        + table(
            [row for row in context.scores if row["kind"] == "rl"],
            [
                ("policy", "Policy"),
                ("seed", "Seed"),
                ("cost_bps", "bps"),
                ("net_return", "Return"),
                ("sharpe", "Sharpe"),
                ("max_drawdown", "MDD"),
                ("trade_count", "Trades"),
                ("active_intervals", "Active"),
                ("flat_decision_fraction", "Flat actions"),
                ("unseen_state_fraction", "Unseen states"),
                ("status", "Status"),
            ],
        )
        + """

### Thống kê qua seed

Mean/median/std chỉ dùng metric hữu hạn; sample std cần ít nhất hai giá trị. Số undefined/infinite/not applicable/insolvent vẫn được báo. Baseline xác định không được nhân bản thành năm mẫu. Random là sanity check. Đây là biến thiên quá trình học trên cùng lịch sử, không phải khoảng tin cậy cho lợi nhuận tương lai.

"""
        + table(
            context.seeds,
            [
                ("policy", "Policy"),
                ("cost_bps", "bps"),
                ("metric", "Metric"),
                ("mean", "Mean"),
                ("median", "Median"),
                ("sample_std", "Std"),
                ("minimum", "Min"),
                ("maximum", "Max"),
                ("finite_count", "Finite"),
                ("undefined_count", "Undefined"),
                ("infinite_count", "∞"),
                ("not_applicable_count", "N/A"),
                ("insolvent_count", "Insolvent"),
            ],
        )
        + """

### Chênh lệch primary − reference cùng seed/cost

"""
        + table(
            context.pairs,
            [
                (key, key)
                for key in (
                    "seed",
                    "cost_bps",
                    "net_return_delta",
                    "sharpe_delta",
                    "max_drawdown_delta",
                    "total_fees_delta",
                    "trade_count_delta",
                    "active_intervals_delta",
                )
            ],
        )
        + """

Sensitivity giữ nguyên Q, nhưng actions có thể đổi vì phí làm equity/exposure/drawdown đi vào state khác. Flat target và exposure trước lệnh là hai đại lượng khác nhau. Nhãn no_trades/sparse_trades/mostly_flat/unseen_states_present/insolvent chỉ giúp diễn giải."""
    )


def yearly_section(context: ReportContext) -> str:
    return (
        """## 8. Theo năm và run kết thúc sớm

Một episode liên tục; returns compound theo năm của end_date, fees theo cùng intervals. Trades đóng trong năm không được dùng để tính calendar return. Coverage phản ánh ngày thực tế; không thêm returns giả cho run insolvent.

"""
        + table(
            [
                row
                for row in context.years
                if row["scenario_id"] in {item["scenario_id"] for item in context.primary}
            ],
            [
                ("scenario_id", "Scenario"),
                ("year", "Year"),
                ("net_return", "Return"),
                ("fees", "Fees"),
                ("active_intervals", "Active"),
                ("closed_trades", "Trades closed"),
                ("start_date", "Start"),
                ("end_date", "End"),
                ("partial_year", "Partial"),
            ],
        )
        + """

Run insolvent: """
        + str(sum((row["status"] == "insolvent" for row in context.scores)))
        + "/"
        + str(len(context.scores))
        + "."
    )


def conclusions_section(context: ReportContext) -> str:
    return f"""## 9. Kết luận, hạn chế và bài học

Primary λ={context.config["primary_lambda"]:g}, seed {context.config["primary_seed"]}, {context.config["primary_cost_bps"]:g} bps: return {display(context.selected, "net_return")}, Sharpe {display(context.selected, "sharpe")}, MDD {display(context.selected, "max_drawdown")}, {context.selected["trade_count"]} trades, active {context.active:.2%} intervals. Reference return {display(context.reference, "net_return")}. Flags primary: {", ".join(context.diagnostics[context.selected["scenario_id"]]["flags"]) or "none"}. Kết quả này phải được đọc cùng mức hoạt động; ít giao dịch chưa đủ bằng chứng về chất lượng dự báo. Không yêu cầu RL thắng baseline để hoàn thành prototype.

Một tài sản, một chuỗi lịch sử, state discretization thô, chế độ thị trường thay đổi và thiếu financing/slippage thực tế giới hạn khả năng suy luận. Chọn λ bằng validation vẫn tạo selection bias; test chỉ được dùng đánh giá protocol đã chốt. Fresh Yahoo download có thể đổi adjustments, nên không thay thế snapshot đã khóa."""


def reproduction_section(context: ReportContext) -> str:
    if context.run_directory is None:
        raise ValueError("Report context needs its actual run directory")
    root = shlex.quote(str(context.run_directory))
    data = shlex.quote(context.protocol["input_file"])
    figure = shlex.quote(str(context.run_directory / "figures/primary.png"))
    risk_lambda = context.config["primary_lambda"]
    cost_bps = context.config["primary_cost_bps"]
    return f"""## 10. Replay and artifacts

```bash
uv sync --python 3.11.16 --frozen --extra dev --extra charts
uv run indexpilot-evaluate run --protocol-dir {root} --data {data}
uv run indexpilot-evaluate verify --protocol-dir {root} --data {data}
uv run indexpilot-evaluate report --protocol-dir {root}
uv run indexpilot-chart --run-dir {root} --save-png {figure}
uv run indexpilot-chart --run-dir {root} --seeds --risk-lambda {risk_lambda:g} --cost-bps {cost_bps:g}
```

Use the frozen calculation revision and exact snapshot for run/verify. Restore the protocol, frozen models, preparation, saved results, and ledger first. These paths record this experiment's locations; when moving machines, substitute restored locations and supply --data with the same snapshot bytes. Hash checks still apply. Report and chart read saved artifacts without training or evaluation. New preparation is a separate experiment; use a new directory and a reason after a completed test.

Artifacts include primary/scenario/seed/paired/yearly tables, diagnostics, protocol, ledger, and each run's equity/ledger/orders/trades/intervals/decisions/transitions. Report/chart only read artifacts. The GUI is optional; PNG rendering supports QT_QPA_PLATFORM=offscreen. Data, models, and detailed outputs stay outside Git and must be archived separately. Future single-asset research includes walk-forward evaluation, additional independent histories, improved state representation, realistic borrow/financing/slippage assumptions, and data-provider archival. These extensions are not part of the frozen experiment."""


def generate_report(run_dir: str | Path, output_path: str | Path | None = None) -> Path:
    root = Path(run_dir)
    context = load_report_context(root)
    sections = [
        f"# Evaluation report: {context.instrument_label}",
        research_section(context),
        data_section(context),
        simulation_section(context),
        learning_section(context),
        protocol_section(context),
        primary_results_section(context),
        robustness_section(context),
        yearly_section(context),
        conclusions_section(context),
        reproduction_section(context),
    ]
    figures = [path for path in sorted((root / "figures").glob("*.png"))]
    if figures and output_path is None:
        sections.append(
            """## Figures

"""
            + """

""".join(f"![{path.stem}](figures/{path.name})" for path in figures)
        )
    destination = Path(output_path) if output_path is not None else root / "report.md"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        """

""".join(sections)
        + """
"""
    )
    return destination
