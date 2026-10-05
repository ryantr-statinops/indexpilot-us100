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

where \(r_{p,t}\) is portfolio return over the holding interval, \(\sigma_t\) is the risk measure, \(c_t\) is transaction cost, and \(\lambda\) is the risk-aversion coefficient. The formula is confirmed. The version 1 definitions below make the terms concrete for the single-stock simulation. Transaction cost is charged once in both portfolio accounting and reward; the risk penalty affects reward only, not account equity.

## Version 1 decision and simulation conventions

These are explicit, simplified version 1 conventions chosen to complete the single-stock learning specification. They are not claims about real brokerage execution and can be revised before Stage 2 implementation.

- **Action:** \(a_t\in[-1,1]\) is signed target notional exposure as a fraction of current equity. -1 means 100% short notional, 0 means flat, and +1 means 100% long notional. Gross exposure is capped at 100%, so no leverage above equity. The continuous interval is the project concept; tabular Q-learning will use the five actions \(\{-1,-0.5,0,0.5,1\}\).
- **Shorting simplification:** short positions are modeled symmetrically through signed returns. Version 1 omits borrow fees, margin calls, forced liquidation, and financing. This is a teaching simulator, not a broker-accurate short account.
- **Observation and execution timing:** at market open \(t\), the agent receives state features calculated only from data through the previous session close, chooses \(a_t\), and rebalances at the current open. The position earns the adjusted-open-to-adjusted-open total return through the next session open. This uses a synthetic adjusted-open price for research accounting; it is not a claim about an executable fill price.
- **Price adjustment:** derive adjusted open as \(\text{Open}\times\text{Adj Close}/\text{Close}\), then calculate adjusted-open-to-adjusted-open return. The adjustment factor incorporates historical distributions/splits in the total-return series; do not separately add dividends to this synthetic-return calculation. Unadjusted OHLC remain available for inspection only.
- **Holdings/cash accounting (Stage 2 revision):** synthetic fractional units `q`, cash `C`, adjusted open `P`; equity is `E=C+qP`. Buy-and-hold preserves units; target exposure rebalances. Cash earns zero; short sale proceeds are cash, not profit.
- **Target after costs:** solve `x=a(E-k|x-v|)` for target notional, with current notional `v=qP`. Trade `delta_q=(x-v)/P`, fee `F=k|x-v|`, then `C'=C-delta_q*P-F`. Target applies to post-fee equity. Fee default is 10 bps, configurable. No separate spread/slippage or financing costs.
- **Reward:** gross return is `q'*(P_next-P)/E_before`; cost fraction is total interval fees / `E_before`; risk is `abs(q'*P/E_before)*s20`. Equity includes fees once; risk affects reward only. Last interval includes terminal liquidation fees.
- **Causal risk:** sample standard deviation (`ddof=1`) of 20 open-to-open returns ending before the decision session. Market features use preceding closes; account state is marked at the current execution quote. No next-open information enters observations.
- **Risk-aversion sweep:** `{0,0.5,1,2}` for later validation experiments; Stage 2 defaults to zero.
- **Limits:** targets are finite and within `[-1,1]`; exposure can drift between decisions. No margin intervention while equity is positive. Non-positive equity triggers liquidation and termination, retaining actual debt and fees.
- **Episode:** contiguous data after warm-up, initially flat with $100,000. Liquidate at the final open without a new decision or artificial return period. Train/validation/test dates remain Stage 4 work.
- **Initial state features:** lagged 1-, 5-, and 20-session adjusted-close returns, 20-session asset volatility, current target exposure, and portfolio drawdown. Each feature is available by the open-time decision; the exact tabular bins are set in Stage 3. No fitted scaler is used in the first tabular version.

## Deferred beyond Stage 1

- Exact chronological train/validation/test dates and walk-forward design (Stage 4).
- Cost sensitivity and any richer slippage/borrow/financing model (Stage 2+).
- Point-in-time US100 membership by market capitalization and reconstitution date. A current list applied to old dates creates survivorship bias (universe extension).

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

In the current AAPL snapshot, adjusted close is 24.1717548370 on 2015-01-02 and 23.4907970428 on 2015-01-05. The simple adjusted-close return is:

```text
23.4907970428 / 24.1717548370 - 1 = -0.02817163 (about -2.8172%)
```

This verifies the return calculation. It does not define an executable strategy or imply that an action could fill at either day's closing price.

For the simulator's adjusted-open convention, adjusted open is 24.6271994096 on 2015-01-02 and 23.9418205485 on 2015-01-05:

```text
23.9418205485 / 24.6271994096 - 1 = -0.02783016 (about -2.7830%)
```

### Position arithmetic illustration

Stage 2 uses synthetic fractional holdings and cash, revising the preliminary exposure-only model. With $100,000 equity, price $100, target +0.5 and a 10bps fee, target notional is `0.5*100000/(1+0.5*0.001) = $49,975.012494`; the fee is $49.975012. The target is 50% of post-fee equity, not exactly $50,000 before fees. Gross holding-period P&L is units times the adjusted-open price change. See [Stage 2 walkthrough](stage-2-simulator.md) for a full entry/exit example and metric definitions.
