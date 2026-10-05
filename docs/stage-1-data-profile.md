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
| Null/non-positive OHLC, adjusted-close, or synthetic adjusted-open rows | 0 |
| Returns | 2,954 simple/log adjusted-close returns and 2,954 synthetic adjusted-open-to-adjusted-open returns; each has one initial null |

The snapshot was fetched on 2026-10-05 at 05:01 UTC, before the U.S. cash session opened that day; the most recent available session was Friday 2026-10-02. Data availability can change independently of this project.

The processed table also includes `adj_open = Open × Adj Close / Close` and `open_to_open_return`. This synthetic adjusted open carries the adjusted-close total-return factor onto the open price so the proposed policy timing has an open-to-open return series. It is not a literal historical fill price.

## Synthetic adjusted-open-to-adjusted-open returns (per observation)

| Statistic | Value |
|---|---:|
| Mean | 0.00105685 |
| Standard deviation (sample) | 0.01868915 |
| 1st percentile | -0.05248516 |
| Median | 0.00136454 |
| 99th percentile | 0.05008418 |

An Augmented Dickey-Fuller diagnostic on this return series produced statistic -33.822680 with 2 lags and 2,951 observations. Its p-value underflowed to 0.0 in floating-point output; that does not mean the true p-value is exactly zero. This is a narrow diagnostic for this downloaded sample under the test's assumptions; it does not show that returns are predictable or that a strategy can earn excess returns.

The data provider can revise adjusted historical prices; these results reflect the snapshot fetched on 2026-10-05 UTC and may change on a later download.

Hand check: adjusted opens were 24.6271994096 on 2015-01-02 and 23.9418205485 on 2015-01-05, giving \(23.9418205485/24.6271994096-1=-0.02783016\) (about -2.7830%).

## Recreate

```bash
uv run indexpilot-fetch --ticker AAPL --start 2015-01-01 --end 2026-10-06 --output-dir data/raw
uv run indexpilot-inspect data/raw/aapl_daily_2015-01-01_to_2026-10-06_processed.parquet
```

Downloaded CSV, Parquet, and manifest are local and ignored by Git. Provider data can be revised, so re-downloading later may not reproduce the exact same snapshot. To reproduce processing from the already archived raw CSV without another download:

```bash
uv run indexpilot-process data/raw/aapl_daily_2015-01-01_to_2026-10-06_raw.csv
```
