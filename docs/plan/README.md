# Project plan

This is a first RL learning project: simulate a stock-positioning task, build a sound baseline, then add RL in small steps. Work through the four stages in order. The initial core experiment uses **one stock**; the eventual **US100** universe and PPO are optional extensions, not prerequisites. In these documents, US100 means the 100 largest U.S.-listed companies by market capitalization at each universe formation date; it does not mean S&P 100 or Nasdaq-100.

## Stages

1. [Foundations and data](stage-1-foundations-and-data.md) — define the toy problem and prepare trustworthy input data.
2. [Simulator and baselines](stage-2-simulator-and-baselines.md) — implement and verify portfolio accounting, costs, metrics, and simple strategies.
3. [Basic RL](stage-3-basic-rl.md) — describe the MDP and train a small discrete-action Q-learning agent, then study reward/risk choices.
4. [Evaluation and wrap-up](stage-4-evaluation-and-wrap-up.md) — run chronological out-of-sample comparisons, document results, and decide whether to extend the scope.

## Definition of done

- The simulator and metrics pass hand-checkable examples.
- RL and baselines use the same data, timing, execution assumptions, and costs.
- Evaluation is chronological and avoids using future information.
- Results include Sharpe, maximum drawdown, CAGR, profit factor, and Calmar, with conventions documented.
- The README/report explains assumptions, limitations, and how to reproduce the experiment.

Stages 1, 2 and 3 are complete. The confirmed reward is `R = gross_portfolio_return - lambda*risk - cost`; Stage 2 defines causal risk and holdings/cash accounting. Stage 3 implements NumPy Q-learning on that simulator. Next is Stage 4 evaluation of the frozen model and protocol on the reserved RL test period. See [Stage 2 walkthrough](../stage-2-simulator.md) for simulator commands and results; see [Stage 3 walkthrough](../stage-3-learning.md) for training and validation.
