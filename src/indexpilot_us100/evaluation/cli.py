"""Run the predeclared baseline suite on a local Stage 1 snapshot."""

import argparse
import tomllib

import polars as pl

from indexpilot_us100.metrics import MetricsReport
from indexpilot_us100.portfolio import (
    SimulationConfig,
    baseline_policies,
    load_market_data,
    run_episode,
)

from .export import export_results


def format_metric(metric, percent=False):
    if metric.status == "positive_infinity":
        return "∞"
    if metric.value is None:
        return "N/A"
    return f"{metric.value:.2%}" if percent else f"{metric.value:.3f}"


def comparison_table(reports: list[MetricsReport]) -> str:
    headers = [
        "Baseline",
        "Final equity",
        "Sharpe",
        "Max DD",
        "CAGR",
        "PF",
        "Calmar",
        "Fees",
        "Trades",
        "Status",
    ]
    rows = []
    for report in reports:
        metrics, summary = report.metrics, report.summary
        rows.append(
            [
                summary["baseline"],
                f"{summary['final_equity']:,.2f}",
                format_metric(metrics["sharpe"]),
                format_metric(metrics["max_drawdown"], True),
                format_metric(metrics["cagr"], True),
                format_metric(metrics["profit_factor"]),
                format_metric(metrics["calmar"]),
                f"{summary['total_fees']:,.2f}",
                str(summary["trade_count"]),
                summary["status"],
            ]
        )
    widths = [max(len(row[i]) for row in [headers, *rows]) for i in range(len(headers))]
    return "\n".join(
        "  ".join(value.ljust(width) for value, width in zip(row, widths))
        for row in [headers, *rows]
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", required=True, help="Stage 1 processed Parquet")
    parser.add_argument("--config", required=True, help="Simulation TOML")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args(argv)
    try:
        config = SimulationConfig.from_toml(args.config)
        market = load_market_data(args.data)
        results = [run_episode(market, policy, config) for policy in baseline_policies()]
        reports = export_results(results, args.data, args.output_dir, args.overwrite)
    except (ValueError, OSError, tomllib.TOMLDecodeError, pl.exceptions.PolarsError) as error:
        parser.error(str(error))
    print(f"Warm-up excluded; {results[0].equity[0]['date']} → {results[0].equity[-1]['date']}")
    print(comparison_table(reports))
    print(f"Artifacts: {args.output_dir}")
    print("Historical baseline diagnostics; not an out-of-sample RL comparison.")
    for warning in market.warnings:
        print(f"Data note: {warning}")
    return 0
