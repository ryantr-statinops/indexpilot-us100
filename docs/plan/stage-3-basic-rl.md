# Stage 3 — Basic RL

## Status

Complete. [MDP contract](../stage-3-mdp.md) and [learning walkthrough/results](../stage-3-learning.md) describe the episode replay schedule, fixed bins, validation protocol and limitations. 129 tests pass. Full AAPL training was repeated and restored models reproduce evaluation. At the Stage 3 checkpoint, RL test data from 2023 was reserved; Stage 4 has since completed the frozen evaluation.

## Goal

Learn the RL loop on the verified simulator with a compact, discrete-action, one-stock problem.

## Define the MDP

Write down \(\mathcal{M}=(S,A,P,R,\gamma)\):

- **State/observation:** lagged market features plus position/portfolio variables needed for the next decision.
- **Action:** discrete target exposures \(\{-1,-0.5,0,0.5,1\}\) as set in Stage 1; short exposure uses synthetic holdings/cash accounting.
- **Transition:** advance one historical step and update accounting.
- **Reward:** use \(R_t=r_{p,t}-\lambda\sigma_t-c_t\) with the causal 20-session risk proxy and actual traded-notional cost. Run a return-only reference (\(\lambda=0\)) and compare with a predeclared \(\lambda\) grid. Keep the risk penalty out of account equity and charge transaction cost exactly once.
- **Discount:** record \(\gamma\) and explain its role for finite episodes.
- **Episode:** contiguous training segment; distinguish natural data end from an artificial time limit.

## Checklist

- [x] Pin down observation/action/reward/execution timing.
- [x] Include prior position if it is needed to calculate costs and preserve the Markov state.
- [x] Confirm no future return or feature appears in an observation.
- [x] Specify observation bounds, data types, scaling, reset, seed, termination, and final-position behavior.
- [x] Implement a small tabular Q-learning agent directly in Python/NumPy: exploration, action selection, update, and terminal handling.
- [x] Test the update on a tiny toy environment with known rewards.
- [x] Compare with Stage 2 baselines using the same simulator.
- [x] Log training reward separately from financial metrics; inspect action frequencies and trades.

## Risk/reward experiment

After return-only Q-learning works:

- [x] Confirm or revise Stage 1's 20-session ex ante volatility proxy and start with \(\lambda\in\{0,0.5,1,2\}\); use validation data for selection.
- [x] Ensure transaction cost enters the accounting/reward path exactly once.
- [x] Compare Sharpe, maximum drawdown, CAGR, profit factor, Calmar, turnover, and costs.
- [x] Look for reward hacking, inactivity, or excessive position churn.

## Deliverables

- Written MDP and environment contract.
- Readable tabular Q-learning implementation and saved configuration/results.
- A baseline comparison and a short explanation of how reward changes behavior.

## Done when

- Environment transitions match the simulator and fixed configurations are reproducible where expected.
- Results separate training reward from trading performance.
- Risk experiments change one design choice at a time.

## Optional tool

Use Gymnasium if a standard environment API helps. It is not necessary to hide the core Q-learning update behind a deep-RL framework.

## Implemented defaults

- Python/NumPy Q table,3840 states ×5 actions; fixed bins, no fitted scaler.
-100 episodes/model; alpha0.1, gamma0.99, epsilon1→0.05 with decay0.97; seed42+episode index.
- Frozen-table exploratory rollout, then chronological off-policy Q updates on reconciled transitions. Terminal updates omit bootstrap.
- Train through2020; validation2021–2022; lambda0/0.5/1/2 ranked by finite greedy validation Sharpe. Reserved RL test is not evaluated.
- Full Stage2 execution/accounting engine; discrete-action adapter with reset/rollout; no separate simulator or Gymnasium dependency.
- NPZ models/visits; training CSV; greedy train/validation transitions and financial reports; diagnostics and selection manifest; FinPlot viewer.

## Acceptance evidence

- Toy Bellman and terminal-bandit tests, simulator parity and terminal fees.
- Changing validation/test prices cannot change trained Q; evaluation does not update visits.
- Two full AAPL trainings produce identical Q/visits/logs/validation summaries; restored-model evaluation gives identical equity.
- Selected lambda2 has only one validation trade and99.8% flat decisions; report records inactivity and sparse-sample metrics explicitly.
- Sharpe-selected validation model is a prototype checkpoint, not a test result. Stage 4 now documents the separately frozen test result.

## Small commits

| # | Commit | Checkpoint |
|---|---|---|
| 01 | `c198277` | docs: define tabular learning and validation protocol |
| 02 | `9db972f` | feat: configure tabular learning experiments |
| 03 | `3592d31` | feat: discretize causal portfolio observations |
| 04 | `da8b90e` | feat: implement tabular q learning updates |
| 05 | `2b3a5b2` | feat: expose finalized trading trajectories |
| 06 | `ab59722` | feat: train and validate risk reward policies |
| 07 | `1ded7f2` | feat: persist learning models and diagnostics |
| 08 | `8a86c4d` | feat: expose tabular training command |
| 09 | `9be22b1` | test: guard learning boundaries and output reuse |
| 10 | `f72f0a0` | feat: view selected policy against baselines |
| 11 | `e668671` | test: handle inactive validation policies explicitly |
| 12 | `e9ceb64` | docs: explain q learning results and inactivity |
| 13 | This documentation checkpoint | docs: mark basic RL complete |
