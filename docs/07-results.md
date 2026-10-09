# 07 — Results and Interpretation

## Contents

- [Experiment reported here](#experiment-reported-here)
- [Validation and selected model](#validation-and-selected-model)
- [Primary test results](#primary-test-results)
- [Primary model activity](#primary-model-activity)
- [Seeds and cost sensitivity](#seeds-and-cost-sensitivity)
- [Primary results by year](#primary-results-by-year)
- [Limitations and lessons](#limitations-and-lessons)
- [Historical AAPL experiment](#historical-aapl-experiment)
- [Verification evidence](#verification-evidence)

## Experiment reported here

This chapter reports the verified **QQQ / Nasdaq-100 ETF** experiment. Tables are read from persisted artifacts; they are not AAPL numbers with a different ticker label. The [predeclared rules](qqq-experiment.md) selected primary lambda 0.5 by QQQ validation and reference lambda 0 before viewing the test.

- Training through 2020; validation 2021-01-04 to 2022-12-30.
- Test **2023-01-03 to 2026-10-02**, 940 open-to-open intervals; 2026 is a partial year.
- Reset flat/$100,000 per run, with the same engine for all policies.
- Ten models and 60 scenarios; all completed with no insolvencies on this snapshot.
- Protocol ID: `16af504702802ec895620d84c64550f5919fbc1933af9151cced8f5c4b8db2dd`.
- Calculation revision: `e2c4cba4f1d51876dad8373d1ffbf41e72050cd0`; [snapshot identity](03-data.md#experiment-snapshot).

Detailed scenario/seed/paired/yearly tables and the generated report are local under `outputs/stage-4/qqq-frozen`, outside Git. QQQ is an ETF proxy; the simulator uses synthetic adjusted prices rather than actual historical fills.

## Validation and selected model

100 episodes per lambda, seed 42, training fees of 10 bps:

| Lambda | Equity USD | Sharpe | MDD | CAGR | Trades |
| --- | --- | --- | --- | --- | --- |
| 0.000 | 101,820.67 | 0.138 | 19.99% | 0.91% | 118 |
| 0.500 | 103,575.88 | 0.545 | 2.99% | 1.79% | 17 |
| 1.000 | 98,959.47 | -0.486 | 1.50% | -0.53% | 8 |
| 2.000 | 100,000.00 | N/A | 0.00% | 0.00% | 0 |

Lambda 0.5 had the highest finite validation Sharpe, approximately 0.545, with 17 trades and 96.02% flat decisions. Lambda 2 stayed entirely flat and had undefined Sharpe. The primary selection was retained for the test; the reference follows the predeclared rule (0 for a nonzero primary). Validation performance does not establish generalization.

## Primary test results

Seed 42, fees of 10 bps, matching intended and actual coverage:

| Policy | Equity USD | Return | Sharpe | MDD | CAGR | PF | Calmar |
| --- | --- | --- | --- | --- | --- | --- | --- |
| q_lambda_0 | 110,783.62 | 10.78% | 0.259 | 23.74% | 2.77% | 1.106 | 0.117 |
| q_lambda_0.5 | 98,873.80 | -1.13% | -0.062 | 7.37% | -0.30% | 0.900 | -0.041 |
| cash | 100,000.00 | 0.00% | N/A | 0.00% | 0.00% | N/A | N/A |
| buy_hold | 285,102.39 | 185.10% | 1.492 | 24.17% | 32.28% | ∞ | 1.335 |
| fixed_long_50 | 171,736.93 | 71.74% | 1.486 | 12.77% | 15.53% | ∞ | 1.217 |
| fixed_short_50 | 55,441.05 | -44.56% | -1.514 | 45.08% | -14.57% | 0.000 | -0.323 |
| sma20_long_flat | 172,382.46 | 72.38% | 1.153 | 18.79% | 15.65% | 1.828 | 0.833 |
| random_discrete | 79,370.74 | -20.63% | -0.356 | 41.43% | -5.98% | 0.910 | -0.144 |

Return/MDD/CAGR are rates; Sharpe/PF/Calmar are ratios. Infinite Profit Factor for a one-trade winning position episode does not mean no drawdown. Cash has undefined Sharpe/PF/Calmar because there is no variation or trade and both CAGR/MDD are zero.

| Policy | Fees USD | Orders | Trades | Active / 940 | Flat actions |
| --- | --- | --- | --- | --- | --- |
| q_lambda_0 | 30,124.88 | 832 | 127 | 849 | 9.68% |
| q_lambda_0.5 | 2,854.80 | 29 | 15 | 15 | 98.40% |
| cash | 0.00 | 0 | 0 | 0 | 100.00% |
| buy_hold | 385.29 | 2 | 1 | 940 | 0.00% |
| fixed_long_50 | 431.43 | 941 | 1 | 940 | 0.00% |
| fixed_short_50 | 554.65 | 941 | 1 | 940 | 0.00% |
| sma20_long_flat | 17,043.51 | 112 | 56 | 645 | 31.38% |
| random_discrete | 81,801.96 | 851 | 450 | 740 | 21.28% |

Buy and hold buys at the first eligible open, keeps units, and sells at the final open. Fixed-exposure policies rebalance each session; scale changes remain in the same directional trade. Full-snapshot Stage 2 baselines run through 2026-10-05 and are separate diagnostics; these tables cover only the frozen test through 2026-10-02.

## Primary model activity

The primary lost **1.13%**, finishing at $98,873.80, with MDD 7.37%, 15 closed trades, and **15/940 active intervals**. Flat decisions accounted for 98.40%; mean gross exposure was 1.49%. Fees totaled $2,854.80. It underperformed cash and buy and hold.

The unseen-state fraction was 3.19%; most decisions still came from states encountered during training. Diagnostic flags: mostly_flat, unseen_states_present. Low exposure is central to interpreting its results; low drawdown alone does not establish predictive skill.

The reference lambda 0 was much more active and earned +10.78% at seed 42/10 bps, but still lagged buy and hold (+185.10%). Neither its positive return nor primary validation Sharpe establishes that the policy outperforms simple baselines.

## Seeds and cost sensitivity

### All RL seeds at 10 bps

| Lambda | Seed | Return | Sharpe | MDD | Trades | Active | Flat actions |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0.000 | 42 | 10.78% | 0.259 | 23.74% | 127 | 849 | 9.68% |
| 0.500 | 42 | -1.13% | -0.062 | 7.37% | 15 | 15 | 98.40% |
| 0.000 | 7 | -19.56% | -0.345 | 42.34% | 170 | 807 | 14.15% |
| 0.500 | 7 | -6.07% | -0.273 | 8.36% | 23 | 23 | 97.55% |
| 0.000 | 21 | -27.39% | -0.555 | 36.12% | 253 | 762 | 18.94% |
| 0.500 | 21 | 0.11% | 0.032 | 5.74% | 19 | 19 | 97.98% |
| 0.000 | 84 | -27.17% | -0.522 | 43.46% | 200 | 781 | 16.91% |
| 0.500 | 84 | -9.80% | -0.379 | 12.57% | 25 | 25 | 97.34% |
| 0.000 | 123 | -27.09% | -0.473 | 42.79% | 255 | 772 | 17.87% |
| 0.500 | 123 | -1.41% | -0.046 | 7.56% | 19 | 19 | 97.98% |

Seed 42 remains primary even when another seed performs better. These seeds represent stochastic learning or random decisions on the same history; they are not independent market samples.

### Net return summaries

| Policy | bps | Mean return | Median | Std (percentage points) | Min | Max |
| --- | --- | --- | --- | --- | --- | --- |
| random_discrete | 0.0 | 33.86% | 38.00% | 26.747 | 5.27% | 70.34% |
| random_discrete | 10.0 | -37.01% | -34.85% | 12.236 | -49.83% | -20.63% |
| random_discrete | 20.0 | -70.36% | -69.24% | 5.600 | -76.09% | -63.02% |
| q_lambda_0 | 0.0 | 11.86% | 8.27% | 15.162 | -0.31% | 37.55% |
| q_lambda_0 | 10.0 | -18.08% | -27.09% | 16.474 | -27.39% | 10.78% |
| q_lambda_0 | 20.0 | -38.77% | -38.23% | 17.795 | -63.54% | -13.89% |
| q_lambda_0.5 | 0.0 | -0.37% | 1.70% | 3.866 | -5.71% | 3.48% |
| q_lambda_0.5 | 10.0 | -3.66% | -1.41% | 4.161 | -9.80% | 0.11% |
| q_lambda_0.5 | 20.0 | -6.01% | -4.53% | 3.149 | -10.60% | -3.14% |

Each row has five finite net returns and no insolvencies. Sample standard deviation is not a confidence interval for future returns. Other metrics can be undefined or infinite; full seed summaries retain all status counts and aggregate finite values only.

### Seed 42 at three fee levels

| Policy | 0 bps | 10 bps | 20 bps |
| --- | --- | --- | --- |
| q_lambda_0 | 37.55% | 10.78% | -13.89% |
| q_lambda_0.5 | 1.70% | -1.13% | -3.87% |
| cash | 0.00% | 0.00% | 0.00% |
| buy_hold | 185.67% | 185.10% | 184.53% |
| fixed_long_50 | 72.28% | 71.74% | 71.19% |
| fixed_short_50 | -44.14% | -44.56% | -44.97% |
| sma20_long_flat | 92.81% | 72.38% | 54.12% |
| random_discrete | 70.34% | -20.63% | -63.02% |

Fees affect equity/account state, so frozen Q does not guarantee identical actions at different costs. Sensitivity reruns the learned policy under each execution assumption; it does not just subtract fees from one equity curve. The primary cost remains 10 bps.

## Primary results by year

| Year | Intervals | Net return | Fees USD | Active | Closed trades | Coverage |
| --- | --- | --- | --- | --- | --- | --- |
| 2023 | 249 | -1.74% | 201.34 | 1 | 1 | As declared for the horizon |
| 2024 | 252 | 1.69% | 493.27 | 3 | 3 | As declared for the horizon |
| 2025 | 250 | 4.56% | 1,340.11 | 7 | 7 | As declared for the horizon |
| 2026 | 189 | -5.36% | 820.07 | 4 | 4 | Partial year |

This is one continuous account without a January 1 reset. Intervals are assigned by end_date, so a December-to-January holding interval belongs to the new year. Annual returns compound to total return. Trade P&L is not a replacement for calendar return; the 2026 result only ends at the October 2 open. Coverage labels refer to declared eligible boundaries, not an exchange-calendar completeness audit.

## Limitations and lessons

- One ETF and one history do not establish performance across market regimes or independent histories.
- QQQ tracks Nasdaq-100 but has its own distributions, fund costs, and tracking characteristics; the experiment does not trade index constituents or the index series directly.
- Fixed coarse state bins approximate the decision problem; they do not establish a Markov price process.
- Validation selection has selection bias; the test evaluates the configuration already chosen.
- Risk penalties can encourage near-flat behavior. Read return/Sharpe alongside exposure, trade counts, fees, and coverage.
- Synthetic adjusted prices and proportional trading fees are simplified execution assumptions; borrow fees, financing, margin calls, and separate slippage are not modeled.
- Historical adjustments can change; fresh Yahoo downloads do not replace a frozen snapshot.

Further single-asset research can examine walk-forward evaluation, independent histories, richer costs, and improved state representation. This experiment validates reproducible accounting/evaluation and does not demonstrate that RL beats the baselines or is profitable live.

## Historical AAPL experiment

AAPL was the earlier single-asset prototype, with its own snapshot, models, and protocol. It remains separate from QQQ. On its 2023-01-03 to 2026-10-02 test at seed 42/10 bps, primary lambda 2 returned −0.76% with 2 active intervals, reference lambda 0 returned −17.42%, and buy and hold returned +159.85%. These are historical AAPL results, not QQQ measurements or a controlled cross-asset ranking.

AAPL protocol: `5fbce9eb3c97815487c57b7eaca4502390562e37ed062609d72c87ba189ec18b`; calculation revision `b6c550d`; archive `outputs/stage-4/aapl-reproduction.tar.gz`. Original detailed tables remain in the AAPL archive. See [historical reproduction](08-reproduction.md#historical-aapl-reproduction).

## Verification evidence

The implementation and clean checkout each passed 206 tests. Independent local replay and relocated clean-environment replay each matched 60/60 scenarios. Account/trade/fee reconciliation, frozen Q/visits, seed-42 checkpoint copies, and offscreen charts were checked. See the [verification record](qqq-verification.md) for exact hashes, tolerances, archive, and performed checks.

**Next:** [reproduction](08-reproduction.md) or the [project README](../README.md).
