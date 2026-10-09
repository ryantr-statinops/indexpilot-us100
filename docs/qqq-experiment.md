# QQQ experiment rules

This protocol is declared before training or viewing QQQ test results. The project studies one asset: QQQ, an ETF tracking the Nasdaq-100. It does not construct a top-100 stock universe. The existing AAPL experiment remains a separate historical experiment.

## Data and boundaries

- Yahoo Finance via yfinance; ticker `QQQ`, daily bars, `auto_adjust=False`, corporate actions enabled.
- Request: 2015-01-01 inclusive to 2026-10-06 exclusive.
- Training through 2020-12-31; validation 2021-01-01 through 2022-12-31; test 2023-01-01 through 2026-10-02.
- Preserve raw CSV, processed Parquet, data manifest, and SHA256 hashes in a separate QQQ directory. Never substitute AAPL data or checkpoints.
- Require adjusted close, finite positive adjusted prices, unique increasing session dates, and coverage through the declared test end. Stop on missing requirements; do not fill prices or shorten the horizon to bypass an error.
- Synthetic adjusted open uses the adjusted-close/raw-close factor. Holdings are synthetic units; distributions are not credited again. This convention is not an actual historical broker fill, and QQQ is an ETF proxy for the index.

## Training and selection

Use the existing `configs/stage-2.toml` and `configs/stage-3.toml`: initial equity $100,000, training fees 10 bps, risk window 20, annualization 252, risk-free rate 0, primary seed 42, 100 episodes per lambda, alpha 0.1, gamma 0.99, epsilon start/decay/floor 1/0.97/0.05, and lambda grid `[0, 0.5, 1, 2]`. Keep the existing fixed state bins, five actions, accounting engine, and validation selection algorithm.

The primary lambda must be the QQQ learning run's validation selection, including its documented undefined-metric fallback. Do not reuse the AAPL selection by assumption. The reference lambda is 0 when primary is nonzero, and 2 when primary is 0. This rule is fixed before test evaluation; never change it based on test performance.

## Frozen evaluation

- Seeds: `[42, 7, 21, 84, 123]`; primary seed 42.
- Costs: `[0, 10, 20]` bps; primary cost 10 bps.
- Two lambda values × five seeds: ten models. Evaluate 30 RL, 15 deterministic baseline, and 15 random baseline scenarios: 60 total.
- Copy the two primary-seed checkpoints from the QQQ learning run. Train eight additional models on the original training segment only.
- Reset each account to flat/$100,000; evaluate greedily with Q/visits read-only.
- Use `outputs/stage-2/qqq-default`, `outputs/stage-3/qqq-default`, and `outputs/stage-4/qqq-frozen`. Preserve AAPL artifacts and ledger history.
- Freeze code, runtime, inputs, selection, models, and configuration before evaluation. Do not alter Python until run and independent verification finish.

## Acceptance

Run relevant unit tests and the existing suite. Check source quality, reconcile account and trade P&L and terminal fees, confirm unchanged Q/visits, independently replay all scenarios, render report/charts, and restore/replay the exact archive in a clean compatible checkout. Record only checks actually performed, including any insolvency or partial coverage. RL profitability or beating a baseline is not an acceptance condition.

Local data, models, and detailed outputs remain outside Git. Publish a verification record and editorial results from checked artifacts. Preserve the package name and existing `indexpilot-*` command names.
