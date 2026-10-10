"""Typed artifacts and finite JSON, with snapshot/config provenance."""

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from dataclasses import asdict
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

import polars as pl

from indexpilot_us100.metrics import compute_metrics, drawdown_curve
from indexpilot_us100.portfolio.simulator import SimulationResult

EVENT_SCHEMA = {
    "sequence": pl.Int64,
    "date": pl.Date,
    "kind": pl.String,
    "price": pl.Float64,
    "cash": pl.Float64,
    "holdings": pl.Float64,
    "equity": pl.Float64,
    "exposure": pl.Float64,
    "fee": pl.Float64,
    "traded_notional": pl.Float64,
}
ORDER_SCHEMA = {
    "sequence": pl.Int64,
    "date": pl.Date,
    "kind": pl.String,
    "price": pl.Float64,
    "target": pl.Float64,
    "delta_units": pl.Float64,
    "units_before": pl.Float64,
    "units_after": pl.Float64,
    "cash_before": pl.Float64,
    "cash_after": pl.Float64,
    "equity_before": pl.Float64,
    "equity_after": pl.Float64,
    "traded_notional": pl.Float64,
    "fee": pl.Float64,
}
TRADE_SCHEMA = {
    "trade_id": pl.Int64,
    "entry_date": pl.Date,
    "direction": pl.Int64,
    "gross_pnl": pl.Float64,
    "fees": pl.Float64,
    "exit_date": pl.Date,
    "net_pnl": pl.Float64,
}
INTERVAL_SCHEMA = {
    "date": pl.Date,
    "end_date": pl.Date,
    **{
        name: pl.Float64
        for name in (
            "start_equity",
            "end_equity",
            "gross_pnl",
            "gross_return",
            "fees",
            "cost_fraction",
            "risk",
            "reward",
            "net_return",
        )
    },
}


def file_hash(path: Path):
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git_revision():
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=Path(__file__).resolve().parents[3],
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
        return result.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None


def write_json(path: Path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def write_json_atomic(path: Path, value):
    """Publish a complete JSON file, preserving the destination on failure."""
    path = Path(path)
    content = json.dumps(value, indent=2, allow_nan=False) + "\n"
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            prefix="." + path.name + "-",
            suffix=".tmp",
            dir=path.parent,
            delete=False,
        ) as file:
            temporary = Path(file.name)
            file.write(content)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def export_results(
    results: list[SimulationResult], input_path: str | Path, output_dir: str | Path, overwrite=False
):
    if not results:
        raise ValueError("No results to export")
    names = [result.baseline for result in results]
    if len(set(names)) != len(names) or any(
        not name or not all(ch.isalnum() or ch in "_-" for ch in name) for name in names
    ):
        raise ValueError("Baseline names must be unique safe directory names")
    if any(result.config != results[0].config for result in results):
        raise ValueError("All baselines must share one configuration")
    output = Path(output_dir)
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        if not overwrite:
            raise ValueError(f"Output exists: {output}; choose a new directory or --overwrite")
        marker = output / "run_manifest.json"
        if (
            output.is_symlink()
            or not marker.is_file()
            or json.loads(marker.read_text()).get("artifact_type") != "indexpilot-stage-2"
        ):
            raise ValueError("Refusing to overwrite a directory without a Stage 2 manifest")
    input_path = Path(input_path).resolve()
    if output.resolve() == input_path or output.resolve() in input_path.parents:
        raise ValueError("Output cannot contain the input data")
    output.parent.mkdir(parents=True, exist_ok=True)
    reports = [compute_metrics(result) for result in results]
    rows = [report.row() for report in reports]
    with tempfile.TemporaryDirectory(prefix=".stage2-", dir=output.parent) as temporary:
        root = Path(temporary)
        for result in results:
            directory = root / result.baseline
            directory.mkdir()
            drawdowns = drawdown_curve([row["equity"] for row in result.ledger])
            equity = [
                {**row, "drawdown": float(drawdowns[row["sequence"]])} for row in result.equity
            ]
            tables = {
                "equity": (
                    equity,
                    {
                        **EVENT_SCHEMA,
                        "net_return": pl.Float64,
                        "reward": pl.Float64,
                        "drawdown": pl.Float64,
                    },
                ),
                "ledger": (result.ledger, EVENT_SCHEMA),
                "orders": (result.orders, ORDER_SCHEMA),
                "trades": (result.trades, TRADE_SCHEMA),
                "intervals": (result.intervals, INTERVAL_SCHEMA),
            }
            for name, (records, schema) in tables.items():
                pl.DataFrame(records, schema=schema).write_parquet(directory / f"{name}.parquet")
        pl.DataFrame(rows, infer_schema_length=None).write_csv(root / "summary.csv")
        write_json(root / "summary.json", rows)
        manifest = dict(
            artifact_type="indexpilot-stage-2",
            schema_version=1,
            created_at=datetime.now(timezone.utc).isoformat(),
            input_file=str(input_path),
            input_sha256=file_hash(input_path),
            configuration=asdict(results[0].config),
            package_version=version("indexpilot-us100"),
            git_revision=git_revision(),
            baselines=[
                dict(
                    name=result.baseline,
                    status=result.status,
                    seed=result.config.seed,
                    start_date=result.equity[0]["date"].isoformat(),
                    end_date=result.equity[-1]["date"].isoformat(),
                    warnings=list(result.warnings),
                )
                for result in results
            ],
        )
        write_json(root / "run_manifest.json", manifest)
        if output.exists():
            shutil.rmtree(output)
        shutil.move(str(root), str(output))
    return reports
