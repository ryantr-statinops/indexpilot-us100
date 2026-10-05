# Stage 4 — Evaluation and wrap-up

## Status

Complete. [Frozen protocol](../stage-4-protocol.md), [reproduction guide](../stage-4-evaluation.md) and [final report](../REPORT.md) document the 10-model/60-scenario experiment. 175 tests pass; AAPL replay, array immutability, ledger reconciliation, figures and clean-environment reproduction are verified.

## Goal

Compare the learned policy fairly on unseen future data, explain what happened, and package a result that can be reproduced.

## Evaluation checklist

- [x] Split train, validation, and final test chronologically.
- [x] Fit preprocessing on training data only; use validation for policy/reward/hyperparameter selection.
- [x] Freeze the chosen setup before using the final test period.
- [x] Keep rolling features causal at boundaries; document position handling between periods.
- [x] Align all strategy results to the same test dates and assumptions.
- [x] Run five fixed seeds and three declared costs, with finite/status counts.
- [x] Preserve an experiment ledger so repeated tuning is visible.
- [x] Report Sharpe, maximum drawdown, CAGR, profit factor, Calmar, equity/drawdown curves, turnover, and costs.
- [x] Analyze unsuccessful runs, unstable behavior, and market periods where the policy struggles.

## Reproducibility and report checklist

- [x] Record Python and dependency versions, data provenance, configuration, random seed, and code revision.
- [x] Provide commands to prepare data, evaluate baselines, train, and run the frozen evaluation.
- [x] Save logs, checkpoints, metric tables, and plot-generating inputs/configurations.
- [x] Explain MDP, timing, execution, costs, short assumptions, data splits, and metric definitions.
- [x] State limitations, including fixed/current-universe survivorship bias if applicable.
- [x] Make claims proportional to the historical simulation; do not present it as evidence of live profitability.

## Final report outline

1. Question and scope.
2. Data and assumptions.
3. Simulator and baselines.
4. MDP and Q-learning design.
5. Evaluation protocol and metrics.
6. Results and diagnostics.
7. Limitations and lessons.
8. Reproduction steps and optional next steps.

Report also contains continuous calendar-year returns, activity/unseen-state diagnostics and paired lambda comparisons.

## Acceptance completed

- [x] A clean setup can reproduce the documented run from the available data/configuration.
- [x] Tables and figures can be regenerated from saved artifacts.
- [x] Conclusions state what the experiment supports and what it does not.

## Possible extensions (only after the core project)

- Expand from one stock to a small group, then to the project-defined US100 universe: the 100 largest U.S.-listed companies by market capitalization at each formation date.
- Define point-in-time membership and a reconstitution schedule. A current list applied historically has survivorship bias. This universe is distinct from the S&P 100 and Nasdaq-100 indices.
- Decide whether a multi-stock action is one selected asset or a vector of portfolio weights.
- Try continuous actions in \([-1,1]\) and PPO with PyTorch/Stable-Baselines3.
- Add richer execution costs, regime features, or walk-forward evaluation.

Primary remains lambda 2/seed 42/10 bps: −0.76% return, 2/940 active intervals. All 60 scenarios completed; no insolvency on this snapshot. Completion depends on verified accounting/reproduction, not beating a baseline.
