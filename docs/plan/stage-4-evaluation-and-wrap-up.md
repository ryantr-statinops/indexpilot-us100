# Stage 4 — Evaluation and wrap-up

## Goal

Compare the learned policy fairly on unseen future data, explain what happened, and package a result that can be reproduced.

## Evaluation checklist

- [ ] Split train, validation, and final test chronologically.
- [ ] Fit preprocessing on training data only; use validation for policy/reward/hyperparameter selection.
- [ ] Freeze the chosen setup before using the final test period.
- [ ] Keep rolling features causal at boundaries; document position handling between periods.
- [ ] Align all strategy results to the same test dates and assumptions.
- [ ] Where time permits, run multiple seeds and report variability.
- [ ] Preserve an experiment ledger so repeated tuning is visible.
- [ ] Report Sharpe, maximum drawdown, CAGR, profit factor, Calmar, equity/drawdown curves, turnover, and costs.
- [ ] Analyze unsuccessful runs, unstable behavior, and market periods where the policy struggles.

## Reproducibility and report checklist

- [ ] Record Python and dependency versions, data provenance, configuration, random seed, and code revision.
- [ ] Provide commands to prepare data, evaluate baselines, train, and run the frozen evaluation.
- [ ] Save logs, checkpoints, metric tables, and plot-generating inputs/configurations.
- [ ] Explain MDP, timing, execution, costs, short assumptions, data splits, and metric definitions.
- [ ] State limitations, including fixed/current-universe survivorship bias if applicable.
- [ ] Make claims proportional to the historical simulation; do not present it as evidence of live profitability.

## Final report outline

1. Question and scope.
2. Data and assumptions.
3. Simulator and baselines.
4. MDP and Q-learning design.
5. Evaluation protocol and metrics.
6. Results and diagnostics.
7. Limitations and lessons.
8. Reproduction steps and optional next steps.

## Done when

- A clean setup can reproduce the documented run from the available data/configuration.
- Tables and figures can be regenerated from saved artifacts.
- Conclusions state what the experiment supports and what it does not.

## Possible extensions (only after the core project)

- Expand from one stock to a small group, then to 100 names.
- Define a point-in-time top-100 universe; a current list applied historically has survivorship bias.
- Decide whether a multi-stock action is one selected asset or a vector of portfolio weights.
- Try continuous actions in \([-1,1]\) and PPO with PyTorch/Stable-Baselines3.
- Add richer execution costs, regime features, or walk-forward evaluation.
