# Stage 3 — Basic RL

## Goal

Learn the RL loop on the verified simulator with a compact, discrete-action, one-stock problem.

## Define the MDP

Write down \(\mathcal{M}=(S,A,P,R,\gamma)\):

- **State/observation:** lagged market features plus position/portfolio variables needed for the next decision.
- **Action:** a few discrete target exposures. Include short/flat/long only if shorting is actually modeled.
- **Transition:** advance one historical step and update accounting.
- **Reward:** use the confirmed form \(R_t=r_{p,t}-\lambda\sigma_t-c_t\). Define the risk measure/window and penalty units before training; transaction costs must enter exactly once. Run a return-only reference as an ablation so the effect of \(\lambda\sigma_t\) can be interpreted.
- **Discount:** record \(\gamma\) and explain its role for finite episodes.
- **Episode:** contiguous training segment; distinguish natural data end from an artificial time limit.

## Checklist

- [ ] Pin down observation/action/reward/execution timing.
- [ ] Include prior position if it is needed to calculate costs and preserve the Markov state.
- [ ] Confirm no future return or feature appears in an observation.
- [ ] Specify observation bounds, data types, scaling, reset, seed, termination, and final-position behavior.
- [ ] Implement a small tabular Q-learning agent directly in Python/NumPy: exploration, action selection, update, and terminal handling.
- [ ] Test the update on a tiny toy environment with known rewards.
- [ ] Compare with Stage 2 baselines using the same simulator.
- [ ] Log training reward separately from financial metrics; inspect action frequencies and trades.

## Risk/reward experiment

After return-only Q-learning works:

- [ ] Choose and document what \(\sigma_t\) means (for example, rolling volatility or a drawdown-based measure), its lookback/timing, and its scale.
- [ ] Add the confirmed risk penalty using a small predeclared range for \(\lambda\), including \(\lambda=0\) as a return-only reference.
- [ ] Ensure transaction cost enters the accounting/reward path exactly once.
- [ ] Compare Sharpe, maximum drawdown, CAGR, profit factor, Calmar, turnover, and costs.
- [ ] Look for reward hacking, inactivity, or excessive position churn.

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
