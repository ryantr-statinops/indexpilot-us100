# Project overview

## Purpose

Learn reinforcement learning through a small, transparent stock-trading simulation. The project should make data timing, portfolio accounting, the MDP, reward, and evaluation understandable before adding complex algorithms or a large universe.

## First version

- Start with one U.S. stock and historical data.
- The intended action is a target position in \([-1,1]\), provisionally meaning maximum short, flat, and maximum long. Stage 1 must pin down the exact meaning and constraints.
- Begin with a few discrete target positions so tabular Q-learning is possible.
- Compare against simple non-RL strategies through the same simulator.
- The eventual **US100 universe** means the 100 largest U.S.-listed companies by market capitalization at each universe formation date. It is a project-defined universe, not the S&P 100 or Nasdaq-100 index. Expand to it only after the one-stock core experiment is sound.

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
- **Reward:** confirmed form \(R_t=r_{p,t}-\lambda\sigma_t-c_t\); the risk measure/window and scaling are defined in Stage 3.
- **Episode:** a contiguous historical segment with explicit start/end behavior.

These details remain provisional until the relevant stage resolves them.

## Metrics

The requested scorecard is Sharpe ratio, maximum drawdown, CAGR, profit factor, and Calmar ratio. Stage 2 defines annualization, risk-free rate, closed-trade accounting, signs, and undefined cases before policies are compared.

## Selected initial stack

| Purpose | Proposed tool |
|---|---|
| Language | Python |
| Numerical computing | NumPy |
| Tabular/dataframe work | Polars |
| Statistical analysis | statsmodels |
| Financial charts | FinPlot |
| First agent | Plain Python/NumPy tabular Q-learning |
| Environment API | Gymnasium, once the MDP is defined |
| Later deep RL option | PyTorch with Stable-Baselines3 PPO; see backend alternatives below |
| Packaging and environment management | `uv` with `pyproject.toml` |
| Verification | pytest for accounting, environment and metric examples |
| Data exploration | JupyterLab; move stable logic into modules |
| Prototype data source | A documented historical-price provider such as `yfinance`; archive snapshots/metadata and verify coverage/terms |
| Versioning | Git; optional GitHub remote |

Add dependencies stage by stage and pin actual versions in `pyproject.toml`. Keep raw downloaded data and generated outputs out of Git unless intentionally reviewed and documented.

### RL framework alternatives

Tabular Q-learning for Stage 3 needs only Python and NumPy; it does not need PyTorch or another deep-learning framework. For later neural-network RL, alternatives include JAX (for example, SBX, which follows the Stable-Baselines API) and TensorFlow (for example, TF-Agents). For this beginner project, keep one framework at most: PyTorch + Stable-Baselines3 is the default if PPO becomes necessary. JAX is a reasonable alternative if learning functional/JIT-based numerical computing is also a goal. Avoid starting with Tensorforce: its own project page says it is no longer maintained.

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
- Which point-in-time source and rebalance schedule will define historical US100 membership and market capitalization? A current list applied throughout history creates survivorship bias.
- What conventions define the five metrics?

Resolve only what the current stage needs. A successful learning project does not need RL to outperform the market; it needs a correct, fair, and interpretable experiment.

## Stage 2 accounting contract

Targets are post-fee equity fractions; holdings/cash and actual traded notional determine P&L and costs. HoldPosition preserves units. Short exposure may drift beyond the target bounds; insolvency closes the position. See `docs/stage-1-assumptions.md` for the revised contract.
