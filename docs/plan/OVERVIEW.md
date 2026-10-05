# Project overview

## Purpose

Learn reinforcement learning through a small, transparent stock-trading simulation. The project should make data timing, portfolio accounting, the MDP, reward, and evaluation understandable before adding complex algorithms or a large universe.

## First version

- Start with one U.S. stock and historical data.
- The intended action is a target position in \([-1,1]\), provisionally meaning maximum short, flat, and maximum long. Stage 1 must pin down the exact meaning and constraints.
- Begin with a few discrete target positions so tabular Q-learning is possible.
- Compare against simple non-RL strategies through the same simulator.
- Consider 100 stocks and continuous-control PPO only after the core experiment is sound.

## Four-stage path

1. **Foundations and data:** define the problem, timing, data source, price/return conventions, and leakage controls.
2. **Simulator and baselines:** implement positions, P&L, costs and metrics; validate with small examples; run simple strategies.
3. **Basic RL:** define state, action, transition, reward and episode; implement tabular Q-learning; add risk penalties as controlled experiments.
4. **Evaluation and wrap-up:** freeze a chronological evaluation protocol, compare out of sample, analyze limitations, and prepare reproducible documentation.

## Initial MDP sketch

- **Agent:** policy selecting a target position.
- **Environment:** historical market data plus portfolio/accounting state.
- **Observation:** lagged market features and current position/portfolio information available at decision time.
- **Action:** initially a small discrete set; later the continuous interval \([-1,1]\).
- **Transition:** market advances and portfolio accounting updates.
- **Reward:** start from next-period portfolio return after trading cost; introduce risk terms separately.
- **Episode:** a contiguous historical segment with explicit start/end behavior.

These details remain provisional until the relevant stage resolves them.

## Metrics

The requested scorecard is Sharpe ratio, maximum drawdown, CAGR, profit factor, and Calmar ratio. Stage 2 defines annualization, risk-free rate, closed-trade accounting, signs, and undefined cases before policies are compared.

## Proposed stack

| Purpose | Proposed tool |
|---|---|
| Language and numerical work | Python, NumPy, pandas |
| Data exploration | JupyterLab; move stable logic into modules |
| Prototype data source | A documented historical-price provider such as `yfinance`; archive snapshots/metadata and verify coverage/terms |
| First agent | Plain Python/NumPy tabular Q-learning |
| Environment API | Gymnasium, when the MDP is defined |
| Later deep RL extension | PyTorch and Stable-Baselines3 PPO |
| Charts | Matplotlib, optionally seaborn |
| Verification | pytest for accounting, environment and metric examples |
| Packaging | `pyproject.toml` with `uv`, or `venv` + pip |
| Versioning | Git; optional GitHub remote |

Do not add every dependency at the start. Pin actual versions when implementation begins. Keep raw downloaded data and generated outputs out of Git unless intentionally reviewed and documented.

## Suggested layout

```text
.
├── README.md
├── pyproject.toml
├── docs/plan/
├── configs/
├── data/                 # local/ignored data
├── notebooks/            # exploration
├── src/indexpilot_us100/
│   ├── data/
│   ├── portfolio/
│   ├── environment/
│   ├── agents/
│   ├── metrics/
│   └── evaluation/
├── tests/
└── outputs/              # local/ignored experiments
```

## Open decisions

- What is the exact existing decision formula?
- Does the action represent a fraction of capital, a share quantity, or leveraged exposure?
- Is shorting included in the first simulation? What financing, margin, and liquidation rules apply?
- What are the observation/execution timestamps, trading frequency, and price field?
- Which date range and data provider will be used?
- Is the eventual 100-stock universe point-in-time by market capitalization, or a fixed snapshot? A current list used throughout history creates survivorship bias.
- What conventions define the five metrics?

Resolve only what the current stage needs. A successful learning project does not need RL to outperform the market; it needs a correct, fair, and interpretable experiment.
