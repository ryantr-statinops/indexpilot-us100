# Stage 1 — Foundations and data

## Goal

Define a small experiment and prepare historical data whose timing and meaning are understood. Keep the first run to one stock.

## Checklist

### Define the task

- [ ] State the learning/research question in one sentence.
- [ ] Recover and record the exact decision formula mentioned in the project discussion; it is not included in the notes available here.
- [ ] Define action \(a_t\in[-1,1]\): target capital exposure, share quantity, or another quantity.
- [ ] Specify whether shorting/leverage is allowed and set position limits. For a first run, long-only is a simpler option.
- [ ] Choose one ticker, date range, and decision frequency.
- [ ] Set the timing: observation → decision → execution price → holding interval → reward.
- [ ] Define initial capital, cash behavior, and episode boundaries.

### Prepare data

- [ ] Select a provider and record retrieval date, terms/access limits, ticker, fields, date range, and timezone.
- [ ] Save the raw snapshot separately from processed data and record a simple manifest/checksum.
- [ ] Choose adjusted-price conventions; handle splits/dividends consistently.
- [ ] Inspect duplicates, missing values, non-trading days, invalid prices, and corporate actions.
- [ ] Compute simple or log returns consistently and verify a few values by hand.
- [ ] Ensure every feature at time \(t\) uses only information available by \(t\).
- [ ] If scaling features, fit scaling parameters on training data only.
- [ ] Keep credentials out of Git and avoid committing bulky/licensed data by default.

## Deliverables

- A short assumptions note with action and event timing.
- A repeatable data-load/download procedure and data manifest.
- A small exploratory notebook or script covering prices, returns, missing data, and basic statistics.

## Done when

- A reader can calculate a position and the next period's return from a tiny example.
- A repeated processing run on the same raw snapshot gives the same data.
- No feature or decision uses future information.

## Keep out of the first pass

The full 100-stock universe, PPO, live trading, and complex market impact. First make one asset understandable and auditable.
