# IndexPilot US100

A learning-focused reinforcement learning project for stock-positioning simulation. The first prototype is one stock (AAPL) with daily historical data. The eventual US100 universe means the 100 largest U.S.-listed companies by market capitalization at each formation date; it is not the S&P 100 or Nasdaq-100 index.

## Current progress

- Project plan: [`docs/plan/README.md`](docs/plan/README.md)
- Stage 1 assumptions and data workflow: [`docs/stage-1-assumptions.md`](docs/stage-1-assumptions.md)
- Stage 1 downloaded-data profile: [`docs/stage-1-data-profile.md`](docs/stage-1-data-profile.md)
- Stage 1 is in progress: the local historical-data snapshot, repeatable processing, and exploratory summary are in place. The reward formula is confirmed; action/execution semantics and the exact risk statistic still need to be finalized. No trading policy or RL agent is implemented yet.

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

`--start` is inclusive and `--end` is exclusive. The command writes a normalized CSV snapshot of the source response, a processed Parquet file with adjusted-close simple/log returns, and a JSON manifest with retrieval parameters, quality checks, package version, and SHA-256 hashes. Downloaded data and its manifest remain local under the ignored `data/` directory; do not commit or redistribute them without checking the provider's terms.

Reprocess the archived CSV without another network request, then inspect the processed file:

```bash
uv run indexpilot-process data/raw/aapl_daily_2015-01-01_to_2026-10-06_raw.csv
uv run indexpilot-inspect data/raw/aapl_daily_2015-01-01_to_2026-10-06_processed.parquet
```

Use `uv run indexpilot-fetch --help` to change ticker, dates, or output directory. The default ticker is AAPL and the default start date is 2015-01-01.

## Data source note

The downloader uses yfinance to access Yahoo Finance data. yfinance is not affiliated with Yahoo and notes that the API is intended for personal use; Yahoo says its Finance data must not be redistributed and is informational, not intended for trading. Review the [yfinance usage note](https://github.com/ranaroussi/yfinance#download-market-data-from-yahoo-finances-api) and [Yahoo data terms](https://uk.help.yahoo.com/kb/exchanges-data-providers-yahoo-finance-sln2310.html) before sharing or using data beyond this local personal project. The snapshot is not a point-in-time US100 constituent history or a live-trading feed. See the assumptions document for current modeling limits and unresolved decisions.

yfinance returns a pandas DataFrame; the downloader uses pandas only at that adapter boundary and normalizes data into Polars immediately for project processing.
