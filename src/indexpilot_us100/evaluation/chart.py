"""Optional FinPlot viewer for persisted equity and drawdown."""

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np
import polars as pl


def load_chart_series(run_dir: str | Path, cost_bps=None, risk_lambda=None, seeds=False):
    root = Path(run_dir)
    manifest = json.loads((root / "run_manifest.json").read_text())
    if manifest.get("artifact_type") == "indexpilot-stage-4":
        from .final.protocol import frozen_path
        from .final.workflow import check_complete

        protocol = json.loads((root / "protocol.json").read_text())
        check_complete(root, protocol)
        config = protocol["evaluation_config"]
        cost = config["primary_cost_bps"] if cost_bps is None else cost_bps
        if cost not in config["costs_bps"]:
            raise ValueError("Cost was not declared in the frozen protocol")
        lam = config["primary_lambda"] if risk_lambda is None else risk_lambda
        rows = [
            row
            for row in manifest["scenarios"]
            if row["cost_bps"] == cost
            and (
                (row["kind"] == "rl" and row["risk_lambda"] == lam)
                if seeds
                else row["seed"] == config["primary_seed"]
            )
        ]
        if not rows:
            raise ValueError("No declared chart scenarios")
        series = []
        for row in rows:
            item = load_chart_series(
                frozen_path(root, "runs/" + row["scenario_id"] + "/accounting")
            )[0]
            item["name"] = (
                row["policy"]
                + (" seed " + str(row["seed"]) if row["kind"] in ("rl", "random") else "")
                + " / "
                + str(cost)
                + " bps"
            )
            series.append(item)
        return series
    if manifest.get("artifact_type") == "indexpilot-stage-3":
        index = manifest["selection"]["selected_index"]
        if type(index) is not int or not 0 <= index < len(manifest["experiments"]):
            raise ValueError("Invalid selected model index")
        directory = manifest["experiments"][index]["model_directory"]
        if not directory or not all(ch.isalnum() or ch in "_-" for ch in directory):
            raise ValueError("Unsafe model directory")
        return load_chart_series(root / directory / "validation")
    if manifest.get("artifact_type") != "indexpilot-stage-2":
        raise ValueError("Expected a Stage 2 run manifest")
    series = []
    for baseline in manifest["baselines"]:
        name = baseline["name"]
        if not name or not all(ch.isalnum() or ch in "_-" for ch in name):
            raise ValueError("Unsafe baseline name")
        table = pl.read_parquet(root / name / "equity.parquet")
        if not {"date", "equity", "drawdown"} <= set(table.columns):
            raise ValueError(f"Missing chart columns for {name}")
        # Exchange session labels, plotted as UTC midnight without intraday meaning.
        seconds = (
            table["date"].cast(pl.Datetime("us")).cast(pl.Int64).to_numpy().astype(float)
            / 1_000_000
        )
        equity = table["equity"].to_numpy()
        drawdown = table["drawdown"].to_numpy() * 100
        if (
            len(seconds) < 2
            or not np.all(np.isfinite(seconds))
            or np.any(np.diff(seconds) <= 0)
            or not np.all(np.isfinite(equity))
            or not np.all(np.isfinite(drawdown))
        ):
            raise ValueError(f"Invalid chart series for {name}")
        series.append(
            dict(
                name=name,
                status=baseline["status"],
                times=seconds,
                equity=equity,
                drawdown=drawdown,
            )
        )
    if not series:
        raise ValueError("No chart series")
    return series


def create_chart(series):
    try:
        import finplot as fplt
    except ImportError as error:
        raise RuntimeError(
            "Install chart dependencies with: uv sync --extra dev --extra charts"
        ) from error
    fplt.legend_text_color = "#222222"
    fplt.legend_fill_color = "#ffffffe6"
    axes = fplt.create_plot("Policy comparison — equity and drawdown (%)", rows=2, maximize=False)
    axes[0].setLabel("left", "Equity", units="USD")
    axes[1].setLabel("left", "Drawdown", units="%")
    for number, item in enumerate(series):
        label = item["name"] + (" [insolvent]" if item["status"] == "insolvent" else "")
        style = "--" if item["name"].startswith("random_discrete") else "-"
        fplt.plot(
            item["times"], item["equity"], ax=axes[0], color=number, legend=label, style=style
        )
        fplt.plot(
            item["times"], item["drawdown"], ax=axes[1], color=number, legend=label, style=style
        )
    return fplt, axes


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--cost-bps", type=float)
    parser.add_argument("--risk-lambda", type=float)
    parser.add_argument("--seeds", action="store_true", help="Show all RL seeds for one lambda")
    parser.add_argument("--save-png", help="Save a Qt-rendered PNG and close")
    args = parser.parse_args(argv)
    try:
        series = load_chart_series(args.run_dir, args.cost_bps, args.risk_lambda, args.seeds)
        if sys.platform.startswith("linux") and not (
            os.environ.get("DISPLAY")
            or os.environ.get("WAYLAND_DISPLAY")
            or os.environ.get("QT_QPA_PLATFORM") == "offscreen"
        ):
            raise RuntimeError(
                "FinPlot needs a desktop display; simulation artifacts remain available."
            )
        fplt, axes = create_chart(series)
    except (OSError, ValueError, RuntimeError, pl.exceptions.PolarsError) as error:
        parser.error(str(error))
    saved = []
    if args.save_png:
        from PyQt6.QtCore import QTimer

        destination = Path(args.save_png)
        destination.parent.mkdir(parents=True, exist_ok=True)
        axes[0].vb.win.resize(1500, 1000)

        def capture():
            saved.append(axes[0].vb.win.grab().save(str(destination)))
            fplt.close()

        QTimer.singleShot(1500, capture)
    fplt.show()
    if args.save_png and not all(saved):
        parser.error("PNG rendering failed")
    return 0
