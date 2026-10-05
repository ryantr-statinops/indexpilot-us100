# Stage 1 data profile — AAPL daily prototype

This is a descriptive snapshot of the locally downloaded AAPL data used to build the Stage 1 pipeline. It is not an investment signal or a strategy backtest.

## Snapshot

| Item | Value |
|---|---|
| Provider | Yahoo Finance via yfinance 0.2.66 |
| Download interval | 1 day |
| Requested dates | 2015-01-01 inclusive through 2026-10-06 exclusive |
| Returned dates | 2015-01-02 through 2026-10-02 |
| Observations | 2,955 daily bars |
| Duplicate session dates | 0 |
| Null/non-positive OHLC and adjusted-close rows | 0 |
| Returns | 2,954 simple and log returns from adjusted close; first observation has no prior return |

The provider has no bar for the exclusive end date, and 2026-10-05 was not present in the returned snapshot. Data availability can change independently of this project.

## Simple adjusted-close returns (per observation)

| Statistic | Value |
|---|---:|
| Mean | 0.00105232 |
| Standard deviation (sample) | 0.01808276 |
| 1st percentile | -0.04831390 |
| Median | 0.00100074 |
| 99th percentile | 0.04849471 |

An Augmented Dickey-Fuller diagnostic on this return series produced statistic -17.657071 and p-value 3.69704e-30 with 8 lags and 2,945 observations. This is a narrow diagnostic for this downloaded sample under the test's assumptions; it does not show that returns are predictable or that a strategy can earn excess returns.

The data provider can revise adjusted historical prices; these results reflect the snapshot fetched on 2026-10-05 UTC and may change on a later download.

## Recreate

```bash
uv run indexpilot-fetch --ticker AAPL --start 2015-01-01 --end 2026-10-06 --output-dir data/raw
uv run indexpilot-inspect data/raw/aapl_daily_2015-01-01_to_2026-10-06_processed.parquet
```

Downloaded CSV, Parquet, and manifest are local and ignored by Git. Provider data can be revised, so re-downloading later may not reproduce the exact same snapshot. To reproduce processing from the already archived raw CSV without another download:

```bash
uv run indexpilot-process data/raw/aapl_daily_2015-01-01_to_2026-10-06_raw.csv
```
