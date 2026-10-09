# 03 — Data and Snapshots

## Contents

- [Source and saved formats](#source-and-saved-formats)
- [Adjusted prices and returns](#adjusted-prices-and-returns)
- [Experiment snapshot](#experiment-snapshot)
- [Quality checks and causal features](#quality-checks-and-causal-features)
- [Splits and warm-up](#splits-and-warm-up)
- [Download and reprocess](#download-and-reprocess)

## Source and saved formats

The pipeline fetches daily QQQ ETF data, a single-asset proxy for the Nasdaq-100, through yfinance with `auto_adjust=False` and corporate actions enabled. pandas receives the provider response; the data is then normalized into Polars.

| Local artifact | Purpose |
|---|---|
| Raw CSV | Normalized snapshot table with OHLC, adjusted close, volume, and available corporate actions |
| Processed Parquet | Typed table with derived adjusted open and returns |
| Data manifest JSON | Parameters, retrieval time, row/date coverage, quality checks, versions, and SHA256 hashes |

Processing requires adjusted close; it raises an error if `adj_close` is missing instead of silently using raw close. Optional corporate-action columns are added with value 0 when the source does not provide them.

The raw CSV is a normalized table, not a byte-for-byte archive of the HTTP response. Source OHLC prices remain unadjusted; the simulator uses separate adjusted columns.

yfinance is an unofficial access route. The project archive is stored locally. See the [yfinance usage notes](https://github.com/ranaroussi/yfinance#download-market-data-from-yahoo-finances-api) and [Yahoo data terms](https://uk.help.yahoo.com/kb/exchanges-data-providers-yahoo-finance-sln2310.html) before sharing data.

## Adjusted prices and returns

For each row:

```text
factor = adj_close / close
adj_open = open * factor
simple_return[i] = adj_close[i] / adj_close[i-1] - 1
log_return[i] = log(adj_close[i] / adj_close[i-1])
open_to_open_return[i] = adj_open[i] / adj_open[i-1] - 1
```

Synthetic adjusted open applies the adjusted-close factor to open. QQQ is an ETF proxy rather than the index series; its observed performance reflects its own distributions and tracking characteristics. It is a price on an adjusted accounting series, not an actual historical fill. The simulator's holdings are **synthetic units** on that series; dividends or splits are not added a second time.

Example from the snapshot:

```text
adj_open on 2015-01-02 = 95.2151710699
adj_open on 2015-01-05 = 94.0497694422
return = 94.0497694422 / 95.2151710699 - 1
       ≈ -1.2240%
```

The return stored at row i describes **open i−1 to open i**. The outcome of an action taken at open i must use **open i to open i+1**. The simulator calculates P&L directly from the two prices it uses; it does not rely on the stored return column for accounting.

## Experiment snapshot

| Property | Saved value |
|---|---|
| Ticker / interval | QQQ / 1d |
| Request | 2015-01-01 inclusive to 2026-10-06 exclusive |
| Actual coverage | 2015-01-02 to 2026-10-05 |
| Rows | 2,956 |
| Open-to-open returns | 2,955; first row is null |
| Duplicate dates | 0 |
| Rows with null or non-positive prices | 0 |
| Retrieved | 2026-10-09, around 07:14 UTC |
| Provider adapter | yfinance 0.2.66 |

Processed file:

```text
data/qqq/qqq_daily_2015-01-01_to_2026-10-06_processed.parquet
SHA256:
4db7a3175dfe288b7a440a2b3cd4996e0322420429fd55feeb3dce8c7d02b9f2
```

The filename records the requested end date, not the last trading date. The final snapshot row (2026-10-05) is outside the frozen test horizon. The experiment ends at the 2026-10-02 open; it does not include that day's open-to-close return. 2026 is a partial year.

The provider may revise historical adjustments. A fresh download for the same ticker and date range can have a different hash, so it cannot replace the exact snapshot in a locked protocol.

## Quality checks and causal features

The market loader requires `date`, `adj_open`, and `adj_close`; dates must be daily Date values, unique, and strictly increasing. Prices must be finite, positive, and non-null. The loader does not sort data, fill prices, create sessions, or fall back to raw open.

Weekends and market holidays are expected. Gaps longer than four calendar days produce a warning; the project does not use an exchange calendar to prove that every session is present.

At the decision on row i:

| Feature | Data used |
|---|---|
| 1/5/20-session returns | Adjusted closes ending at i−1 |
| Prior close / SMA20 | Close at i−1 / mean of the 20 closes before i |
| Risk volatility | Sample standard deviation, ddof=1, of 20 open returns ending before open i |
| Account state | Cash, holdings, equity, exposure, and drawdown marked at quote open i |

Open i is used to mark the account; open i+1 is not in the observation. The agent's bins are fixed and are not fit on validation or test data.

The inspect command runs a statsmodels ADF test on open returns. In this snapshot, the sample mean is about 0.00079225 and the standard deviation is about 0.01367566; the ADF statistic is about −60.124156. This diagnostic does not establish that returns are predictable. A displayed p-value of 0 due to floating-point underflow does not mean the mathematical p-value is exactly zero.

## Splits and warm-up

| Segment | Declared boundary | Evaluated coverage |
|---|---|---|
| Training | Through 2020-12-31 | 2015-02-03 to 2020-12-31; 1,489 intervals |
| Validation | 2021-01-01 to 2022-12-31 | 2021-01-04 to 2022-12-30; 502 intervals |
| Test | 2023-01-01 to 2026-10-02 | 2023-01-03 to 2026-10-02; 940 intervals |

The default risk window is 20. The first eligible decision needs `max(20, risk_window)+1` preceding rows; with a 20-session window, index 21 is the first decision and at least 23 rows are needed for one holding interval.

Validation and test use history before their boundary for warm-up, but those sessions are not included in the equity curve or metrics. Each segment's account resets to flat with $100,000; holdings are not carried from training or validation into the test.

## Download and reprocess

Example of fetching a **new snapshot** into a separate directory so the archived input is not replaced:

```bash
uv run indexpilot-fetch --ticker QQQ --start 2015-01-01 --end 2026-10-06 --output-dir data/new-snapshot
uv run indexpilot-inspect data/new-snapshot/qqq_daily_2015-01-01_to_2026-10-06_processed.parquet
```

The downloader's default end is the current UTC date, exclusive. To reprocess an archived raw CSV:

```bash
uv run indexpilot-process data/qqq/qqq_daily_2015-01-01_to_2026-10-06_raw.csv --output data/reprocessed/qqq.parquet
```

Reprocessing does not need Yahoo or network access. Check the Parquet hash if you intend to use it for exact reproduction; do not assume that an equivalent table has identical bytes.

The earlier AAPL snapshot and hashes remain part of the historical experiment; they must not be used as QQQ inputs. See [verification evidence](qqq-verification.md) for the QQQ protocol and checked archive.

Related: [scope and architecture](01-overview.md).

**Next:** the [project README](../README.md) links to the simulator and reproduction chapters.
