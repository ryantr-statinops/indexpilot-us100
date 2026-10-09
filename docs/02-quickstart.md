# 02 — Quickstart

## Contents

- [Set up the environment](#set-up-the-environment)
- [Read the existing results](#read-the-existing-results)
- [View and verify the locked experiment](#view-and-verify-the-locked-experiment)
- [Learn from a new snapshot](#learn-from-a-new-snapshot)
- [Command reference](#command-reference)

## Set up the environment

You need Git and uv. Run all commands below from the repository root:

```bash
git clone https://github.com/ryantr-statinops/indexpilot-us100.git
cd indexpilot-us100
uv sync --python 3.11.16 --frozen --extra dev
```

To use FinPlot:

```bash
uv sync --python 3.11.16 --frozen --extra dev --extra charts
```

Python 3.11.16 is the numerical runtime used by the locked experiment. The project declares Python ≥3.11; exact replay checks the runtime more strictly.

QQQ is the default download ticker and the single-asset Nasdaq-100 ETF proxy. A Git clone does not contain local data, checkpoints, or results. If you only want to understand the project, start with [results](07-results.md); if you want to run it, choose the workflow below.

## Read the existing results

The QQQ primary model (lambda 0.5, seed 42, 10 bps) returned −1.13% and was active for 15/940 intervals. The reference model (lambda 0) returned +10.78%; buy and hold returned +185.10% over the test period 2023-01-03 to 2026-10-02. 2026 is a partial year.

[Results and interpretation](07-results.md) includes metrics, seeds/costs, and activity. The generated full report and accounting tables are stored locally under `outputs/stage-4/qqq-frozen`.

## View and verify the locked experiment

**Prerequisites:** restore the archived snapshot, protocol, frozen models, preparation, saved runs/summaries/manifest, and ledger using the [archive restoration guide](08-reproduction.md#restore-the-archive-in-a-clean-checkout).

After restoring:

```bash
uv run indexpilot-evaluate report --protocol-dir outputs/stage-4/qqq-frozen
uv run indexpilot-chart --run-dir outputs/stage-4/qqq-frozen
```

The report is written to `outputs/stage-4/qqq-frozen/report.md`; the chart opens equity/drawdown plots for the eight primary policies. These commands read saved results.

To run or verify the **frozen QQQ experiment**, use code compatible with revision `e2c4cba4f1d51876dad8373d1ffbf41e72050cd0`, Python 3.11.16, and its frozen lockfile. Documentation-only changes on main remain compatible; later Python/lock changes may require a separate frozen checkout. Run these commands after restoring the QQQ archive:

```bash
uv run indexpilot-evaluate run \
  --protocol-dir outputs/stage-4/qqq-frozen \
  --data data/qqq/qqq_daily_2015-01-01_to_2026-10-06_processed.parquet

uv run indexpilot-evaluate verify \
  --protocol-dir outputs/stage-4/qqq-frozen \
  --data data/qqq/qqq_daily_2015-01-01_to_2026-10-06_processed.parquet
```

For a completed run, `run` checks hashes and reuses the saved results; `verify` computes them independently for comparison. Do not run `prepare` in the restored directory. Passing `--data` lets a new machine use a relocated snapshot with the expected hash.

For example, read the primary table with:

```python
import polars as pl

summary = pl.read_csv("outputs/stage-4/qqq-frozen/primary_summary.csv")
print(summary.select("policy", "net_return", "sharpe", "trade_count", "active_intervals"))
```

Interpret null metrics together with their corresponding `<metric>_status` fields; the report displays them as N/A or ∞.

## Learn from a new snapshot

This workflow needs a network connection for the fetch step and creates a **different experiment**; it does not replace the input to the old protocol:

```bash
uv run indexpilot-fetch --ticker QQQ --start 2015-01-01 --end 2026-10-06 --output-dir data/demo
uv run indexpilot-inspect data/demo/qqq_daily_2015-01-01_to_2026-10-06_processed.parquet

uv run indexpilot-simulate \
  --data data/demo/qqq_daily_2015-01-01_to_2026-10-06_processed.parquet \
  --config configs/stage-2.toml \
  --output-dir outputs/stage-2/qqq-demo

uv run indexpilot-chart --run-dir outputs/stage-2/qqq-demo
```

The simulator exports a summary and equity/ledger/orders/trades/interval tables for six baselines. The output directory must be new; use a different name for subsequent attempts.

To observe the learning loop:

```bash
uv run indexpilot-train \
  --data data/demo/qqq_daily_2015-01-01_to_2026-10-06_processed.parquet \
  --config configs/stage-3.toml \
  --output-dir outputs/stage-3/qqq-demo

uv run indexpilot-chart --run-dir outputs/stage-3/qqq-demo
```

Training runs 100 episodes for each lambda in the grid and selects by validation. A chart of a learning run opens the selected model's validation results; it is not the final test.

A fresh download can change adjustments/hashes, metrics, and the selected lambda. Final evaluation preparation currently requires the source selection to match the primary lambda in the config; a mismatch stops preparation. For a new final experiment, use the fresh learning run's validation selection as primary and the [predeclared reference rule](qqq-experiment.md), then create a separate config/protocol before viewing test results. The published config `configs/stage-4-qqq.toml` records primary 0.5/reference 0 for the exact archived QQQ source. To reproduce that result, restore its archive and exact hashes.

For example, an order can target +0.5 without holdings ending up at 500 units: units depend on price, the current account, and fees. See the [simulator chapter](04-simulator.md) for the accounting details.

## Command reference

```bash
uv run indexpilot-fetch --help
uv run indexpilot-process --help
uv run indexpilot-inspect --help
uv run indexpilot-simulate --help
uv run indexpilot-train --help
uv run indexpilot-evaluate --help
uv run indexpilot-evaluate prepare --help
uv run indexpilot-chart --help
```

Simulation, learning, and evaluation parameters are stored in version-controlled TOML files; do not change a run by editing its outputs. Synthetic tests can run with `uv run pytest -q` without Yahoo or a market snapshot.

The earlier AAPL experiment remains available through [historical reproduction](08-reproduction.md#historical-aapl-reproduction). Its data and models are separate from QQQ.

**Next:** read [data](03-data.md) to understand prices/timing and [reproduction](08-reproduction.md) to restore and troubleshoot the experiment.
