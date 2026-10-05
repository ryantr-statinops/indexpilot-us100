# IndexPilot US100

A learning-focused reinforcement learning project for stock-positioning simulation. The first prototype is one stock (AAPL) with daily historical data. The eventual US100 universe means the 100 largest U.S.-listed companies by market capitalization at each formation date; it is not the S&P 100 or Nasdaq-100 index.

## Current progress

- Project plan: [`docs/plan/README.md`](docs/plan/README.md)
- Stage 1 assumptions and data workflow: [`docs/stage-1-assumptions.md`](docs/stage-1-assumptions.md)
- Stage 1 downloaded-data profile: [`docs/stage-1-data-profile.md`](docs/stage-1-data-profile.md)
- Stage 1 is complete: AAPL data pipeline, action/reward definitions, causal observation timing, and episode/accounting conventions are documented. Stage 2 is complete: holdings/cash simulator, six baseline policies, five metrics, audited exports and FinPlot viewer. 103 automated tests pass. Stage 3 is complete: NumPy tabular Q-learning, fixed causal state bins, episode replay, a validation-only lambda sweep, saved models and diagnostics. 129 tests pass. Stage 4 evaluation on the reserved RL test period is next.

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

Training uses data through2020 and validation2021–2022. The RL test period from2023 is reserved. Selection favors lambda2 on validation Sharpe, but that policy is flat99.8% of decisions and has only one validation trade; see the report before interpreting the metrics. Output directories are local and not committed.
