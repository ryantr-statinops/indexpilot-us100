# Stage 1 — Foundations and data

## Goal

Define a small experiment and prepare historical data whose timing and meaning are understood. Keep the first run to one stock.

## Checklist

### Define the task

- [x] State the learning/research question in one sentence; see [`../stage-1-assumptions.md`](../stage-1-assumptions.md).
- [x] Record the confirmed reward formula `R_t = r_{p,t} - λσ_t - c_t`; see [`../stage-1-assumptions.md`](../stage-1-assumptions.md). The risk statistic/window is deferred to Stage 3.
- [ ] Confirm the proposed interpretation of action \(a_t\in[-1,1]\) as signed target notional exposure; see [`../stage-1-assumptions.md`](../stage-1-assumptions.md).
- [ ] Specify whether shorting/leverage is allowed and set position limits. For a first run, long-only is a simpler option.
- [x] Choose one ticker, date range, and decision frequency for the data prototype: AAPL, daily, requested from 2015-01-01.
- [ ] Set the timing: observation → decision → execution price → holding interval → reward.
- [ ] Define initial capital, cash behavior, and episode boundaries.

### Prepare data

- [x] Select a prototype provider and record retrieval date, ticker, fields, date range, and daily session-date semantics. Review provider terms before redistribution or other use.
- [x] Save a normalized source snapshot separately from processed data and record a manifest/checksum.
- [x] Choose an adjusted-price convention for return features; corporate actions are saved, while OHLC remain unadjusted and are not yet used for P&L.
- [x] Inspect duplicate dates, null values, non-trading-day handling, invalid prices, and corporate-action fields.
- [x] Compute adjusted-close simple/log returns and verify a sample by hand.
- [ ] Ensure every feature at time \(t\) uses only information available by \(t\).
- [ ] If scaling features, fit scaling parameters on training data only.
- [x] Keep credentials out of Git and downloaded data local/ignored by default.

## Deliverables

- A short assumptions note with current data conventions and unresolved action/execution timing.
- A repeatable data-load/download procedure and data manifest.
- A small exploratory notebook or script covering prices, returns, missing data, and basic statistics.

The `indexpilot-inspect` command is the Stage 1 exploratory script; see [`../stage-1-data-profile.md`](../stage-1-data-profile.md) for the current snapshot summary.

## Done when

- A reader can calculate a position and the next period's return from a tiny example.
- A repeated processing run on the same raw snapshot gives the same data.
- No feature or decision uses future information.

## Keep out of the first pass

The full US100 universe, PPO, live trading, and complex market impact. Here, US100 means the 100 largest U.S.-listed companies by market capitalization at each universe formation date, not the S&P 100 or Nasdaq-100 index. First make one asset understandable and auditable.
