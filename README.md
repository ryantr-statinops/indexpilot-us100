# IndexPilot US100

A reinforcement learning prototype that simulates **daily AAPL positions** with NumPy tabular Q-learning and an accounting simulator for holdings and cash. The project focuses on understanding agent decisions, reconciling trade accounting, and producing reproducible evaluations.

**Current status: all four stages of the AAPL prototype are complete**, covering data, the simulator and baselines, Q-learning, and frozen evaluation. US100 is a planned extension; it is not the universe currently being simulated.

## What the project does

- Downloads and normalizes price data, then saves snapshots and hashes for input verification.
- Simulates long, short, and flat positions, fractional units, rebalancing, trading fees, and liquidation.
- Runs six baselines and a Q-learning agent through the same accounting engine.
- Evaluates Sharpe ratio, maximum drawdown, CAGR, Profit Factor, and Calmar ratio.
- Provides traceability through the ledger, orders, trades, transitions, and activity diagnostics.
- Offers command-line tools, FinPlot equity/drawdown charts, and reproducible locked experiments.

## Key results

Test period **2023-01-03 to 2026-10-02**, 940 open-to-open intervals; initial equity $100,000, seed 42, and fees of 10 bps. 2026 is a partial year.

| Policy | Net return | Position-active intervals / 940 |
|---|---:|---:|
| Primary RL — lambda 2 | −0.76% | 2 |
| Reference RL — lambda 0 | −17.42% | 760 |
| Buy and hold | +159.85% | 940 |

The primary model is almost always flat; its low drawdown comes with very low exposure. These results do not show that RL beats the baseline or has predictive skill. See [results and interpretation](docs/07-results.md) for validation, seeds, and cost sensitivity.

The current validation suite has **191 passing tests**. The experiment contains **10 models and 60 scenarios**, with account/trade P&L reconciliation, unchanged Q/visit tables during evaluation, and an independent replay in a clean checkout and environment.

## Quickstart

You need Git and uv. From the repository root, install the environment and chart dependencies:

```bash
uv sync --python 3.11.16 --frozen --extra dev --extra charts
```

**To view the completed experiment:** restore the saved artifacts using the [reproduction guide](docs/08-reproduction.md), then run:

```bash
uv run indexpilot-evaluate report --protocol-dir outputs/stage-4/aapl-frozen
uv run indexpilot-chart --run-dir outputs/stage-4/aapl-frozen
```

Data, checkpoints, and detailed outputs are not included in a Git clone. The local experiment archive is `outputs/stage-4/aapl-reproduction.tar.gz`; obtain and restore that archive separately. The report and chart commands read saved results; they do not train or reevaluate policies.

To recompute the published AAPL experiment, use a **separate checkout at revision `b6c550d`**, restore the exact snapshot and models as described in the reproduction guide, then run this command from that checkout. The current main branch has been hardened and has a different calculation fingerprint; it can still read and report the old artifacts.

```bash
uv run indexpilot-evaluate verify --protocol-dir outputs/stage-4/aapl-frozen --data data/raw/aapl_daily_2015-01-01_to_2026-10-06_processed.parquet
```

To start with a new snapshot, see the [full quickstart](docs/02-quickstart.md). A fresh Yahoo download may have different historical adjustments and a different hash; it does not automatically reproduce the old experiment. Synthetic tests can run with `uv run pytest -q` without Yahoo or network access.

## Tech stack

| Role | Technology |
|---|---|
| Language / locked numerical runtime | Python 3.11.16 |
| Numerical computing, state encoding, and Q-learning | NumPy |
| Dataframes and CSV/Parquet | Polars |
| Statistical diagnostics | statsmodels |
| Price source / adapter | yfinance / pandas |
| Charts | FinPlot and Qt, optional `charts` extra |
| Packaging / validation | uv, uv.lock / pytest |

The current agent does not need PyTorch or Gymnasium. pandas is used at the yfinance and chart adapters; core data processing and exports use Polars.

## Documentation

- [Overview](docs/01-overview.md): goals, scope, stack, and architecture.
- [Quickstart](docs/02-quickstart.md): installation, commands, and viewing results.
- [Results](docs/07-results.md): metrics, activity, stability, and lessons.
- [Reproduction](docs/08-reproduction.md): archive restoration, hashes, verification, and troubleshooting.

The [documentation index](docs/README.md) provides reading paths and chapters on data, the simulator, Q-learning, and evaluation.

## Limitations and future work

The prototype uses one asset, synthetic adjusted prices, and simple proportional costs. Short positions have no borrow fees, financing, or margin calls. This is an educational simulation, not a live-trading system.

The planned US100 universe is the 100 largest U.S.-listed companies by market capitalization on each formation date; it is not the Nasdaq-100 or S&P 100. Point-in-time membership, multi-asset allocation, walk-forward evaluation, richer costs, and PPO are possible extensions beyond the current prototype.
