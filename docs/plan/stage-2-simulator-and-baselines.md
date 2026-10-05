# Stage 2 — Simulator and baselines

## Goal

Build deterministic portfolio accounting and evaluation measures before training an RL policy.

## Simulator checklist

- [ ] Specify the per-step order: observe → choose target → execute → pay costs → hold through return → update equity.
- [ ] Define how target position maps to holdings, cash, and exposure.
- [ ] Implement P&L for the supported position types; if shorting is deferred, state that clearly.
- [ ] Calculate turnover consistently from position changes.
- [ ] Apply a configurable simple trading cost; specify whether spread/slippage are included.
- [ ] Enforce exposure limits and define behavior at zero/negative equity.
- [ ] Decide whether open positions are liquidated at episode end and include any cost.
- [ ] Keep simulator logic independent of notebooks and agents.

## Baselines

Implement several simple policies through the **same** execution and cost code:

- [ ] Flat/cash.
- [ ] Buy-and-hold or fixed exposure, where supported by the action constraints.
- [ ] A simple periodic rebalance or transparent signal policy if useful.
- [ ] Random actions only as an environment sanity check, not as a serious financial benchmark.

## Metric checklist

Implement and document the requested metrics:

- [ ] **Sharpe:** return frequency, annualization factor, risk-free rate, and zero-volatility behavior.
- [ ] **Maximum drawdown:** report convention consistently as a positive magnitude or negative return.
- [ ] **CAGR:** elapsed-time convention and behavior for non-positive equity.
- [ ] **Profit factor:** define how position changes/reversals form closed trades; handle no-loss cases.
- [ ] **Calmar:** CAGR divided by absolute drawdown magnitude; define zero-drawdown behavior.
- [ ] Include equity and drawdown curves, evaluation dates, trade count, and costs alongside summary metrics.

## Verification examples

- [ ] Hold a position through one known return.
- [ ] Enter and exit with a known cost.
- [ ] Reverse position if shorting is supported.
- [ ] Hit an exposure cap.
- [ ] End an episode with an open position.
- [ ] Test metric functions on small synthetic sequences with hand-computed answers.

## Deliverables

- Deterministic simulator and baseline policies.
- Metrics module and a standard comparison table.
- Automated tests for accounting and metric edge cases.

## Done when

- Accounting reconciles with hand calculations.
- Flat behavior and cost treatment match the documented assumptions.
- Every baseline uses the same dates, execution timing, and cost assumptions.
