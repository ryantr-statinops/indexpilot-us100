# IndexPilot US100

A learning-focused reinforcement learning project for stock-positioning simulation. The first prototype is one stock (AAPL) with daily historical data. The eventual US100 universe means the 100 largest U.S.-listed companies by market capitalization at each formation date; it is not the S&P 100 or Nasdaq-100 index.

## Current progress

- Project plan: [`docs/plan/README.md`](docs/plan/README.md)
- Stage 1 assumptions and data workflow: [`docs/stage-1-assumptions.md`](docs/stage-1-assumptions.md)
- Stage 1 downloaded-data profile: [`docs/stage-1-data-profile.md`](docs/stage-1-data-profile.md)
- **Stage 1 complete:** causal AAPL data pipeline and modeling assumptions.
- **Stage 2 complete:** holdings/cash accounting, six baselines, five metrics and FinPlot.
- **Stage 3 complete:** NumPy Q-learning, frozen state bins and validation-only lambda selection.
- **Stage 4 complete:** locked test protocol, 10 models, 60 seed/cost scenarios, immutable greedy evaluation, activity/yearly diagnostics and independent replay.
- **175 tests pass**, including a fresh checkout/environment. [Final report](docs/REPORT.md) and [Stage 4 reproduction guide](docs/stage-4-evaluation.md).

## Setup

Install [`uv`](https://docs.astral.sh/uv/) and run:

```bash
uv sync
```

The lockfile produced by `uv lock` pins the resolved dependency versions. FinPlot is an optional charting extra and can be added when charts are needed:

```bash
uv sync --extra charts
```

## Download the prototype data

```bash
uv run indexpilot-fetch --ticker AAPL --start 2015-01-01 --end 2026-10-06 --output-dir data/raw
```

`--start` is inclusive and `--end` is exclusive. The command writes a normalized CSV snapshot of the source response, a processed Parquet file with adjusted-close simple/log returns plus synthetic adjusted-open/open-to-open return columns, and a JSON manifest with retrieval parameters, quality checks, package version, and SHA-256 hashes. Downloaded data and its manifest remain local under the ignored `data/` directory; do not commit or redistribute them without checking the provider's terms.

Reprocess the archived CSV without another network request, then inspect the processed file:

```bash
uv run indexpilot-process data/raw/aapl_daily_2015-01-01_to_2026-10-06_raw.csv
uv run indexpilot-inspect data/raw/aapl_daily_2015-01-01_to_2026-10-06_processed.parquet
```

Use `uv run indexpilot-fetch --help` to change ticker, dates, or output directory. The default ticker is AAPL and the default start date is 2015-01-01.

## Data source note

The downloader uses yfinance to access Yahoo Finance data. yfinance is not affiliated with Yahoo and notes that the API is intended for personal use; Yahoo says its Finance data must not be redistributed and is informational, not intended for trading. Review the [yfinance usage note](https://github.com/ranaroussi/yfinance#download-market-data-from-yahoo-finances-api) and [Yahoo data terms](https://uk.help.yahoo.com/kb/exchanges-data-providers-yahoo-finance-sln2310.html) before sharing or using data beyond this local personal project. The snapshot is not a point-in-time US100 constituent history or a live-trading feed. See the assumptions document for current modeling limits and unresolved decisions.

yfinance returns a pandas DataFrame; the downloader uses pandas only at that adapter boundary and normalizes data into Polars immediately for project processing.

## Simulate and inspect baselines

See the [Stage 2 walkthrough](docs/stage-2-simulator.md) for accounting examples, metric conventions, local AAPL results, and fee sensitivity.

```bash
uv sync --extra dev
uv run pytest -q
uv run indexpilot-simulate --data data/raw/aapl_daily_2015-01-01_to_2026-10-06_processed.parquet --config configs/stage-2.toml --output-dir outputs/stage-2/aapl-default
uv sync --extra dev --extra charts
uv run indexpilot-chart --run-dir outputs/stage-2/aapl-default
```

Use a new output directory or `--overwrite` for an existing Stage 2 run. The simulator requires a local Stage 1 snapshot; charts additionally require a desktop display. Outputs stay local. Baseline results on the full historical sample are diagnostics, not an out-of-sample RL evaluation.

## Train basic RL

The [Stage 3 walkthrough](docs/stage-3-learning.md) explains the Q update, training schedule, split dates, saved models and observed inactivity.

```bash
uv run indexpilot-train --data data/raw/aapl_daily_2015-01-01_to_2026-10-06_processed.parquet --config configs/stage-3.toml --output-dir outputs/stage-3/aapl-default
uv run indexpilot-chart --run-dir outputs/stage-3/aapl-default
```

Training uses data through 2020 and validation 2021–2022. Selection favors lambda 2 on validation Sharpe, with one validation trade and 99.8% flat decisions. Stage 4 has evaluated the predeclared test from 2023; selection is unchanged. Output directories are local and not committed.


## Final evaluation and report

Actual test coverage: **2023-01-03 → 2026-10-02**, 940 intervals; 2026 is incomplete. Primary lambda 2/seed 42/10 bps returned **−0.76%**, with only **2 active intervals**; reference lambda 0 returned **−17.42%**. Buy-and-hold returned **+159.85%**. Read activity, seed/cost variability and limitations alongside the financial metrics.

```bash
uv sync --python 3.11.16 --frozen --extra dev --extra charts
uv run indexpilot-evaluate prepare --data data/raw/aapl_daily_2015-01-01_to_2026-10-06_processed.parquet --source-run outputs/stage-3/aapl-default --config configs/stage-4.toml --output-dir outputs/stage-4/aapl-frozen
uv run indexpilot-evaluate run --protocol-dir outputs/stage-4/aapl-frozen
uv run indexpilot-evaluate verify --protocol-dir outputs/stage-4/aapl-frozen
uv run indexpilot-evaluate report --protocol-dir outputs/stage-4/aapl-frozen
uv run indexpilot-chart --run-dir outputs/stage-4/aapl-frozen
```

Preparation requires an unused output directory, the Stage 3 source artifacts and the exact archived snapshot. For the existing experiment, run/verify reuse the frozen inventory; no training occurs. A completed run is integrity-checked before reuse. Verification recomputes separately. Creating another protocol after test completion requires an explicit reason.

Data, checkpoints and detailed results remain local outside Git. The local archive `outputs/stage-4/aapl-reproduction.tar.gz` packages the matching snapshot and artifacts; see the reproduction guide for restoring them and using `--data` when the snapshot moves. A new Yahoo download is not assumed identical.

The four-stage AAPL prototype is complete. Historical US100 membership, multi-asset allocation, PPO and walk-forward are backlog items.
