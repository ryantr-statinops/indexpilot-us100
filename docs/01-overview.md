# 01 — Project Overview

## Contents

- [Problem and results](#problem-and-results)
- [Simulation scope](#simulation-scope)
- [Implemented stack](#implemented-stack)
- [Architecture and data flow](#architecture-and-data-flow)
- [How to read the project](#how-to-read-the-project)

## Problem and results

IndexPilot US100 is a project for learning reinforcement learning through simulated stock-position decisions. The current prototype uses **daily QQQ ETF data as a Nasdaq-100 proxy**: each session, a policy chooses a short, flat, or long exposure target, and the simulator tracks cash, holdings, fees, and equity.

The research question is whether a Q-learning policy trained on older history can retain its performance on later data compared with simple baselines.

QQQ validation selected lambda 0.5. On the frozen test, the primary returned −1.13% with 15/940 active intervals, while buy and hold returned +185.10%. The primary is mostly flat and does not beat cash or buy and hold on this test. The prototype's value is its ability to explain each decision, reconcile the accounting, and reproduce the experiment; completion does not require RL to be profitable.

For example, action +0.5 means setting the long position's value to 50% of equity **after fees**. It does not mean buying 50% of capital on every session. Action 0 closes the position; −0.5 creates a short position equal to 50% of post-fee equity.

## Simulation scope

| Item | Convention |
|---|---|
| Implemented asset | One ticker: QQQ (Nasdaq-100 ETF proxy) |
| Frequency | Daily, held from the current open to the next open |
| Simulated trading price | Synthetic adjusted open |
| Account | Cash and synthetic units; fractional units are allowed |
| Initial capital | $100,000, starting flat in each episode |
| Agent | NumPy tabular Q-learning with five actions |
| Evaluation | Training through 2020, validation in 2021–2022, test from 2023 |
| Completed prototype | Data pipeline, simulator, baselines, agent, frozen evaluation, report, and charts |

The project now focuses on one asset representing **Nasdaq-100 through QQQ**. It does not select or trade 100 companies individually. The earlier plan to build a universe from the largest U.S.-listed companies has been retired. The repository/package name `indexpilot-us100` and existing CLI names remain for compatibility. AAPL remains a separate historical experiment with its original archive and protocol.

The short model has no borrow fees, financing, or margin calls; trading fees are a simple rate on traded notional. There is no live execution, PPO, or walk-forward evaluation. QQQ has ETF-specific distributions and tracking characteristics; the price convention uses synthetic adjusted prices rather than actual broker fills.

## Implemented stack

| Role | Technology and use |
|---|---|
| Language | Python; the locked experiment uses 3.11.16 |
| Numerical computing and agent | NumPy arrays in float64, RNG, Q table, and state encoding |
| Data and exports | Polars for CSV, typed Parquet, and result tables |
| Statistical diagnostics | statsmodels Augmented Dickey-Fuller test in the inspect command |
| Price source | yfinance accesses Yahoo Finance |
| Data adapters | pandas at the yfinance and chart boundaries; Polars remains the core dataframe library |
| Charts | FinPlot, Qt/PyQt6; optional `charts` extra |
| Packaging | uv, `pyproject.toml`, and `uv.lock` |
| Validation | pytest; the current suite has 206 tests |

The current agent does not need PyTorch or Gymnasium. The environment uses its own episode API; statsmodels is not used to choose actions or train Q.

The QQQ frozen evaluation uses [stage-4-qqq.toml](../configs/stage-4-qqq.toml); Stage 2/3 settings remain shared. The implemented configuration is in [configs](../configs/); dependencies and entry points are in [pyproject.toml](../pyproject.toml). Use the lockfile to recreate the numerical environment instead of selecting new library versions.

## Architecture and data flow

```text
Yahoo/yfinance
    ↓ normalize pandas → Polars
raw CSV + processed Parquet + data manifest
    ↓ validate dates/prices, causal features
MarketData + portfolio simulator
    ├── six baseline policies → accounting artifacts + metrics
    └── TradingEnvironment → finalized transitions
             ↓ Q-learning updates after rollout
        checkpoints + training logs + validation selection
             ↓ freeze inventory/config/data/code hashes
        60 test scenarios → summaries + diagnostics
             ↓ read persisted artifacts
        report + equity/drawdown charts
```

Responsibilities in [src/indexpilot_us100](../src/indexpilot_us100/):

| Module | Responsibility |
|---|---|
| `data` | Download, process, and inspect snapshots |
| `portfolio` | Account, execution, interval transitions, trades, and simulator |
| `environment` | Adapter that creates RL transitions from the simulator |
| `agents` | Bins/actions, Q-learning, and training |
| `metrics` | Sharpe, MDD, CAGR, Profit Factor, and Calmar |
| `evaluation` | CLI, exports, charts, and frozen final evaluation |

RL and baselines use the **same accounting engine**. The risk penalty changes only the reward; financial metrics are calculated from the post-fee account.

Data, checkpoints, and outputs are stored locally in Git-ignored directories. A repository clone contains code, configuration, and documentation, but not the experiment inputs.

## How to read the project

To learn the project, follow data → simulator → Q-learning → evaluation → results. To replay the experiment, start with the prerequisites and locked archive; a fresh download does not guarantee the same bytes or historical adjustments.

The [experiment rules](qqq-experiment.md) record pre-test choices, and [verification evidence](qqq-verification.md) records the completed checks.

**Next:** the [project README](../README.md) links to the documentation index and run instructions.
