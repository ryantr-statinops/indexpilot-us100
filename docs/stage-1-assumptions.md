# Stage 1 assumptions and data workflow

## Prototype scope

- **Research question:** Can a tabular RL policy trained on one stock's daily history learn a position policy with a better return/risk trade-off than simple fixed-exposure baselines on later data?
- **Learning objective:** build an auditable historical data pipeline and understand how observations and returns are represented before implementing a trading policy or RL agent.
- **Instrument:** AAPL, selected as a single-stock prototype. This is not a claim that AAPL represents the eventual US100 universe.
- **Frequency/date range:** daily bars starting 2015-01-01. The downloader defaults its exclusive end date to the current UTC date, so it does not request a potentially incomplete current-day bar.
- **Provider:** Yahoo Finance accessed through yfinance. This is an unofficial route; retrieval may change or fail. yfinance notes that the API is intended for personal use, while Yahoo says its Finance data must not be redistributed and is for information, not trading. Review the [yfinance usage note](https://github.com/ranaroussi/yfinance#download-market-data-from-yahoo-finances-api) and [Yahoo data terms](https://uk.help.yahoo.com/kb/exchanges-data-providers-yahoo-finance-sln2310.html); local downloaded files are excluded from Git.
- **Source response:** downloaded with `auto_adjust=False` and corporate actions enabled. The local raw CSV stores a normalized snapshot of returned OHLC, adjusted close, volume, dividend, split, and capital-gains fields when available; it is not a byte-for-byte HTTP/API response archive.
- **Processed prices:** simple and log returns are calculated from `Adj Close`; the OHLC fields remain unadjusted source values. Do not use the raw OHLC for P&L across splits/dividends without defining and applying a consistent adjustment convention.
- **Missing dates:** weekends and exchange holidays are naturally absent; no rows are synthesized. Missing values, duplicate dates, and non-positive prices are recorded in the manifest for inspection.
- **Date labels:** daily dates are U.S. exchange session labels; intraday timezone handling is outside this daily prototype.
- **Persistence:** raw CSV, processed Parquet, and JSON manifest are stored under `data/`, which is ignored by Git. The manifest records parameters, retrieval time, row/date coverage, quality checks, package version, and SHA-256 hashes.
- **Dataframe adapter:** yfinance returns pandas-formatted data; pandas is an explicit compatibility dependency at the download boundary, after which values are normalized into Polars for processing.

## Confirmed reward formula

The reward is:

\[
R_t = r_{p,t} - \lambda\sigma_t - c_t
\]

where \(r_{p,t}\) is portfolio return over the reward interval, \(\sigma_t\) is the chosen risk measure, \(c_t\) is transaction cost, and \(\lambda\) is the risk-aversion coefficient. The formula is confirmed; the exact risk measure/window and scaling of its penalty remain to be specified in Stage 3. Transaction cost must be represented consistently and subtracted only once. This reward formula defines how the agent is scored; it does not by itself define how an action maps into a market position.

## Not yet specified

- The exact risk statistic/window for \(\sigma_t\), units/normalization for \(\lambda\), and precise transaction-cost model for \(c_t\) will be selected in later stages.
- **Proposed action interpretation, pending confirmation:** \(a_t\in[-1,1]\) is signed target notional exposure as a fraction of current equity; -1 is 100% short notional, 0 is flat, +1 is 100% long notional, and absolute gross exposure cannot exceed 100%. The first simulator would omit borrowing fees, margin calls, and liquidation mechanics unless these are added deliberately.
- **Proposed timing, pending confirmation:** at market open \(t\), form the observation using information through the previous session close, set the target position at that open, and measure the holding-period outcome to the next session open. The historical open-price adjustment/corporate-action accounting still needs a consistent Stage 2 convention.
- The exact training/evaluation date splits and selected feature set are deferred to later stages.
- The future US100 membership must be point-in-time by market capitalization and reconstitution date. A current list applied to historical dates would create survivorship bias.

## Reproducible commands

```bash
uv sync
uv run indexpilot-fetch --ticker AAPL --start 2015-01-01 --end 2026-10-06 --output-dir data/raw
uv run indexpilot-process data/raw/aapl_daily_2015-01-01_to_2026-10-06_raw.csv
uv run indexpilot-inspect data/raw/aapl_daily_2015-01-01_to_2026-10-06_processed.parquet
```

Replace the exclusive end date with the next calendar date when refreshing data after the date shown above. Do not commit raw market data or manifest files without reviewing source terms and privacy implications.

## Hand-checkable examples

### Return calculation

In the current AAPL snapshot, adjusted close is 24.1717548370 on 2015-01-02 and 23.4907932281 on 2015-01-05. The simple adjusted-price return is:

```text
23.4908008575 / 24.1717643738 - 1 = -0.02817186 (about -2.8172%)
```

This verifies the return calculation. It does not define an executable strategy or imply that an action could fill at either day's closing price.

### Position arithmetic illustration (not yet the trading rule)

If starting equity is $100,000 and a future simulator convention defines target exposure as 0.5, then target notional is $50,000. At a hypothetical fill price of $100, that corresponds to 500 shares before costs. If those shares are held while price moves to $102, gross P&L is $1,000, or 1% of starting equity before cash yield, dividends, fees, and any other assumptions. This is a sizing illustration, not a finalized execution/accounting rule.
