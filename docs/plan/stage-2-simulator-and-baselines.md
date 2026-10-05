# Stage 2 — Simulator and baselines

## Status

Complete. See [walkthrough, conventions and audited AAPL results](../stage-2-simulator.md). 103 automated tests pass; FinPlot desktop rendering and AAPL 0/10/20bps sensitivity were verified.

## Goal

Build deterministic portfolio accounting and evaluation measures before training an RL policy.

## Simulator checklist

- [x] Specify the per-step order: observe → choose target → execute → pay costs → hold through return → update equity.
- [x] Define how target position maps to holdings, cash, and exposure.
- [x] Implement P&L for the supported position types; if shorting is deferred, state that clearly.
- [x] Calculate turnover consistently from position changes.
- [x] Apply a configurable simple trading cost; specify whether spread/slippage are included.
- [x] Enforce exposure limits and define behavior at zero/negative equity.
- [x] Decide whether open positions are liquidated at episode end and include any cost.
- [x] Keep simulator logic independent of notebooks and agents.

## Baselines

Implement several simple policies through the **same** execution and cost code:

- [x] Flat/cash.
- [x] Buy-and-hold or fixed exposure, where supported by the action constraints.
- [x] A simple periodic rebalance or transparent signal policy if useful.
- [x] Random actions only as an environment sanity check, not as a serious financial benchmark.

## Metric checklist

Implement and document the requested metrics:

- [x] **Sharpe:** return frequency, annualization factor, risk-free rate, and zero-volatility behavior.
- [x] **Maximum drawdown:** report convention consistently as a positive magnitude or negative return.
- [x] **CAGR:** elapsed-time convention and behavior for non-positive equity.
- [x] **Profit factor:** define how position changes/reversals form closed trades; handle no-loss cases.
- [x] **Calmar:** CAGR divided by absolute drawdown magnitude; define zero-drawdown behavior.
- [x] Include equity and drawdown curves, evaluation dates, trade count, and costs alongside summary metrics.

## Verification examples

- [x] Hold a position through one known return.
- [x] Enter and exit with a known cost.
- [x] Reverse position if shorting is supported.
- [x] Hit an exposure cap.
- [x] End an episode with an open position.
- [x] Test metric functions on small synthetic sequences with hand-computed answers.

## Deliverables

- Deterministic simulator and baseline policies.
- Metrics module and a standard comparison table.
- Automated tests for accounting and metric edge cases.

## Done when

- Accounting reconciles with hand calculations.
- Flat behavior and cost treatment match the documented assumptions.
- Every baseline uses the same dates, execution timing, and cost assumptions.

## Implementation map

- `portfolio/config.py`: validated TOML configuration.
- `portfolio/market.py`: strict Parquet input and causal market features.
- `portfolio/account.py`: fractional units/cash and analytical post-fee targets.
- `portfolio/transition.py`: interval P&L, risk/reward and liquidation.
- `portfolio/records.py`, `trades.py`: event/order ledgers and net position-episode trades.
- `portfolio/simulator.py`, `baselines.py`: reusable runner and six policies.
- `metrics/`: scorecard and explicit undefined/infinite states.
- `evaluation/`: typed exports, simulation CLI and optional FinPlot viewer.

## Acceptance evidence

- Hand example: $100,000 → target+1 at$100 → exit at$110 with10bps → $109,780.219780.
- Cash remains$100,000 with no orders; buy-and-hold has exactly entry and liquidation orders.
- Trade P&L and interval fees reconcile with account/order records in synthetic fixtures and AAPL.
- Causal prefix checks, invalid targets, equity insolvency, seed reset and optional chart dependencies are tested.
- Summary JSON/CSV and selected Parquet artifacts match byte-for-byte on repeated AAPL runs.
- Final liquidation charges fees inside the last interval; risk penalties never alter equity.
- Target bounds apply at execution; short drift is allowed. Early insolvency has its own coverage/status.
- Full-sample AAPL comparisons are diagnostics. Stages 3 and 4 have since completed training/validation and the separately frozen test evaluation.

## Small commit sequence

Each code checkpoint includes relevant tests. Initial pushes waited for SSH unlocking; authenticated HTTPS was then used to publish the preserved individual commits.

| # | Commit | Checkpoint |
|---|---|---|
| 01 | `8fe6434` | docs: define stage 2 accounting contract |
| 02 | `9e31bd6` | feat: add simulation configuration |
| 03 | `26304f7` | feat: validate simulation market data |
| 04 | `dfed588` | feat: align causal simulation windows |
| 05 | `40c0490` | feat: add portfolio account valuation |
| 06 | `688a0ce` | feat: rebalance targets without costs |
| 07 | `157cfae` | feat: charge turnover costs on rebalances |
| 08 | `90e109d` | feat: record accounting events |
| 09 | `bab706f` | feat: advance portfolio through one interval |
| 10 | `7775fcf` | feat: calculate interval risk and reward |
| 11 | `4716f1d` | feat: finalize and terminate episodes |
| 12 | `2dbe734` | feat: track position episode trades |
| 13 | `eba16be` | feat: run deterministic policy episodes |
| 14 | `18b8ed3` | feat: add cash and buy hold baselines |
| 15 | `5809894` | feat: add fixed exposure baselines |
| 16 | `916fd69` | feat: add causal sma and random baselines |
| 17 | `6259af4` | feat: calculate equity and drawdown metrics |
| 18 | `625abbc` | feat: calculate sharpe and cagr |
| 19 | `3cfb29d` | feat: calculate profit factor and calmar |
| 20 | `d6ed04c` | feat: export simulation results |
| 21 | `2ea9fb9` | feat: expose baseline simulation cli |
| 22 | `eaf6c91` | feat: add finplot result viewer |
| 23 | `951d706` | test: verify full simulator reconciliation |
| 24 | `5713c32` | docs: add stage 2 walkthrough and results |
| 25 | This documentation checkpoint | docs: mark stage 2 complete |
