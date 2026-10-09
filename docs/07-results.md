# 07 — Results and Interpretation

## Contents

- [Experiment reported here](#experiment-reported-here)
- [Validation and selected model](#validation-and-selected-model)
- [Primary test results](#primary-test-results)
- [Primary model activity](#primary-model-activity)
- [Seeds and cost sensitivity](#seeds-and-cost-sensitivity)
- [Primary results by year](#primary-results-by-year)
- [Limitations and lessons](#limitations-and-lessons)
- [Verification evidence](#verification-evidence)

## Experiment reported here

The results below are read from saved artifacts; the policies are not rerun. The [frozen protocol](06-evaluation.md) defines primary lambda 2/seed 42/10 bps and reference lambda 0; these choices were not changed after viewing the test.

- Training: through the end of 2020; actual validation coverage 2021-01-04 to 2022-12-30.
- Test: **2023-01-03 to 2026-10-02**, 940 open-to-open intervals; 2026 is a partial year.
- Each run resets to $100,000; all policies use the same engine.
- 10 models and 60 scenarios; all completed, with no insolvencies on this snapshot.
- Protocol ID: `5fbce9eb3c97815487c57b7eaca4502390562e37ed062609d72c87ba189ec18b`.
- Calculation revision: `b6c550d`; see [snapshot SHA256 and convention](03-data.md#experiment-snapshot).

The tables here select information needed to interpret the results. Full scenario/seed/paired/yearly tables and the generated report are stored locally under `outputs/stage-4/aapl-frozen`; they are not committed to the docs.

## Validation and selected model

100 episodes per lambda, seed 42, fees of 10 bps:

| Lambda | Equity USD | Sharpe | MDD | CAGR | Trades |
|---|---:|---:|---:|---:|---:|
| 0.0 | 88,470.96 | -0.162 | 32.56% | -5.98% | 174 |
| 0.5 | 103,386.52 | 0.297 | 8.23% | 1.69% | 34 |
| 1.0 | 103,687.96 | 0.595 | 2.05% | 1.84% | 4 |
| 2.0 | 103,584.38 | 0.698 | 0.05% | 1.79% | 1 |

Lambda 2 had the highest validation Sharpe, but only **one trade** and 99.80% flat decisions. That trade ran from 2022-02-24 to 2022-02-25 and had net P&L of about $3,584.38. Infinite Profit Factor or high Calmar alongside one trade does not demonstrate predictive skill.

The selection was retained for test evaluation. A strong validation result does not guarantee a strong test result.

## Primary test results

Seed 42, fees of 10 bps, same intended/actual coverage:

| Policy | Equity USD | Return | Sharpe | MDD | CAGR | PF | Calmar |
|---|---:|---:|---:|---:|---:|---:|---:|
| q_lambda_0 | 82,583.96 | -17.42% | -0.196 | 35.69% | -4.98% | 0.908 | -0.140 |
| q_lambda_2 | 99,239.61 | -0.76% | -0.479 | 0.90% | -0.20% | 0.111 | -0.225 |
| cash | 100,000.00 | 0.00% | N/A | 0.00% | 0.00% | N/A | N/A |
| buy_hold | 259,848.56 | 159.85% | 1.074 | 33.33% | 29.04% | ∞ | 0.871 |
| fixed_long_50 | 166,436.56 | 66.44% | 1.069 | 17.87% | 14.57% | ∞ | 0.816 |
| fixed_short_50 | 55,309.02 | -44.69% | -1.094 | 46.14% | -14.63% | 0.000 | -0.317 |
| sma20_long_flat | 180,613.50 | 80.61% | 0.962 | 27.12% | 17.10% | 2.080 | 0.631 |
| random_discrete | 141,276.23 | 41.28% | 0.550 | 29.09% | 9.66% | 1.130 | 0.332 |

Return/MDD/CAGR are rates; Sharpe/PF/Calmar are ratios. Infinite PF for buy and hold and fixed long 50 means one closed position episode was profitable; it does not mean there was no drawdown. Cash has N/A for Sharpe/PF/Calmar because it has no variation/trades and both CAGR/MDD are zero.

| Policy | Fees USD | Orders | Trades | Active/940 | Flat actions |
|---|---:|---:|---:|---:|---:|
| q_lambda_0 | 45,755.41 | 655 | 266 | 760 | 19.15% |
| q_lambda_2 | 199.43 | 4 | 2 | 2 | 99.79% |
| cash | 0.00 | 0 | 0 | 0 | 100.00% |
| buy_hold | 360.01 | 2 | 1 | 940 | 0.00% |
| fixed_long_50 | 496.73 | 941 | 1 | 940 | 0.00% |
| fixed_short_50 | 686.97 | 941 | 1 | 940 | 0.00% |
| sma20_long_flat | 11,287.85 | 80 | 40 | 575 | 38.83% |
| random_discrete | 96,136.87 | 851 | 450 | 740 | 21.28% |

Buy and hold buys at the start, holds the units, and sells at the end; fixed exposure rebalances every session. Order count and trade count can therefore differ greatly even when there is only one long-position episode. Full-sample baselines from 2015 were used to check the simulator; the tables above cover only the locked experiment's test segment.

## Primary model activity

Lambda 2 lost **0.76%**, ending with equity of $99,239.61, below cash and buy and hold. Its MDD of only 0.90% came with **2/940 active intervals** and **938/940 flat actions**.

Both trades targeted 50% long and each lasted one interval:

| Open → close | Gross P&L USD | Fees USD | Net P&L USD |
|---|---:|---:|---:|
| 2025-01-03 → 2025-01-06 | +195.09 | 100.15 | +94.94 |
| 2026-02-13 → 2026-02-17 | −756.04 | 99.29 | −855.33 |

The second row's gross loss and opening/closing fees combine to a net loss of $855.33. The two net P&Ls sum to about −$760.39, matching final equity minus initial capital.

The primary's unseen-state fraction was 2.55%; most flat decisions were still in states seen during training. A strong volatility penalty encourages avoiding exposure. With so few trades, the metrics do not provide enough evidence of predictive skill; low drawdown should not be interpreted as a strategy better than cash.

Lambda 0 was active for 760 intervals, closed 266 trades, paid about $45,755.41 in fees, and lost 17.42%. The gap from training performance illustrates the risk of repeatedly fitting to one history and poor generalization.

## Seeds and cost sensitivity

### All RL seeds at 10 bps

| Lambda | Seed | Return | Sharpe | MDD | Trades | Active | Flat actions |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0.0 | 42 | -17.42% | -0.196 | 35.69% | 266 | 760 | 19.15% |
| 2.0 | 42 | -0.76% | -0.479 | 0.90% | 2 | 2 | 99.79% |
| 0.0 | 7 | -13.24% | -0.083 | 47.07% | 218 | 793 | 15.64% |
| 2.0 | 7 | -2.06% | -0.618 | 2.34% | 2 | 3 | 99.68% |
| 0.0 | 21 | -29.65% | -0.350 | 45.63% | 241 | 781 | 16.91% |
| 2.0 | 21 | -1.03% | -0.618 | 1.17% | 2 | 3 | 99.68% |
| 0.0 | 84 | -27.97% | -0.397 | 43.96% | 249 | 701 | 25.43% |
| 2.0 | 84 | -1.52% | -0.479 | 1.81% | 2 | 2 | 99.79% |
| 0.0 | 123 | -29.94% | -0.385 | 52.06% | 268 | 786 | 16.38% |
| 2.0 | 123 | 0.78% | 0.155 | 1.71% | 3 | 4 | 99.57% |

Seed 42 remains primary; it was not replaced with seed 123 after seeing a positive return. All lambda-2 runs were sparse/mostly flat. Random seed 42 also made money on the test, which is not enough to establish quality: the mean of five random seeds at 10 bps was −22.46%, with sample standard deviation of 38.92 percentage points.

### Net return summaries

| Policy | bps | Mean return | Median | Std (percentage points) | Min | Max |
|---|---:|---:|---:|---:|---:|---:|
| random_discrete | 0 | 64.93% | 61.16% | 83.90 | -3.00% | 203.22% |
| random_discrete | 10 | -22.46% | -23.19% | 38.92 | -54.58% | 41.28% |
| random_discrete | 20 | -63.54% | -63.39% | 18.06 | -78.73% | -34.18% |
| q_lambda_0 | 0 | 26.89% | 22.81% | 31.93 | -11.42% | 72.43% |
| q_lambda_0 | 10 | -23.64% | -27.97% | 7.77 | -29.94% | -13.24% |
| q_lambda_0 | 20 | -46.72% | -50.23% | 10.21 | -57.72% | -34.52% |
| q_lambda_2 | 0 | -0.56% | -0.83% | 1.16 | -1.67% | 1.38% |
| q_lambda_2 | 10 | -0.92% | -1.03% | 1.07 | -2.06% | 0.78% |
| q_lambda_2 | 20 | -1.27% | -1.23% | 1.00 | -2.45% | 0.17% |

Each row uses all five seeds and five finite net returns; none were insolvent. This is the sample standard deviation of stochastic training outcomes on the **same history**, not a confidence interval for future returns. Other metrics may be undefined or infinite; the full `seed_summary` retains status counts and aggregates finite values only.

### Seed 42 at three fee levels

| Policy, seed 42 | 0 bps | 10 bps | 20 bps |
|---|---:|---:|---:|
| q_lambda_0 | 72.43% | -17.42% | -34.52% |
| q_lambda_2 | -0.56% | -0.76% | -0.96% |
| cash | 0.00% | 0.00% | 0.00% |
| buy_hold | 160.37% | 159.85% | 159.33% |
| fixed_long_50 | 67.06% | 66.44% | 65.81% |
| fixed_short_50 | -44.18% | -44.69% | -45.20% |
| sma20_long_flat | 95.66% | 80.61% | 66.73% |
| random_discrete | 203.22% | 41.28% | -34.18% |

Fees change equity/account state; a frozen Q table does not guarantee identical actions across cost scenarios. Sensitivity therefore evaluates the same learned policy under different execution assumptions, instead of only subtracting additional fees from one equity curve. Costs of 0/20 bps were not used to choose a favorable fee level; the primary result remains at 10 bps.

## Primary results by year

| Year | Intervals | Net return | Fees USD | Active | Closed trades | Coverage |
|---|---:|---:|---:|---:|---:|---|
| 2023 | 249 | 0.00% | 0.00 | 0 | 0 | As declared for the horizon |
| 2024 | 252 | 0.00% | 0.00 | 0 | 0 | As declared for the horizon |
| 2025 | 250 | 0.09% | 100.15 | 1 | 1 | As declared for the horizon |
| 2026 | 189 | -0.85% | 99.29 | 1 | 1 | Partial year |

This is one continuous account; it does not reset on January 1. Intervals are assigned by **end_date**, so an interval from the final December open to the first January open belongs to the new year. Annual returns compound to total return; trade P&L is not used in place of calendar return.

There were no trades in 2023–2024; that is a result worth reporting. The 2026 return only runs through the October 2 open and should not be compared as a full calendar year.

## Limitations and lessons

- One AAPL ticker and one history do not represent US100 or every market regime.
- Validation-based selection has selection bias; the test checks only this fixed protocol.
- The 3,840 bins combine distinct situations; the Q table does not prove that prices are Markov.
- The per-interval risk proxy and large lambda can make the agent almost always flat.
- Synthetic prices, proportional fees, and shorts without financing/borrow/margin modeling differ from brokerage conditions.
- Seed variability does not replace independent market histories or walk-forward evaluation.
- Historical adjustments can be revised; a fresh Yahoo download is not exact reproduction.

The main lesson is to read return/Sharpe alongside exposure, trade counts, fees, and coverage. The prototype validates the accounting and evaluation mechanics; these results do not support a claim that RL beats the baselines or is profitable in live trading.

Possible extensions include point-in-time US100 membership, multi-asset actions, walk-forward evaluation, richer costs, and PPO. These are extensions, not part of the experiment currently being run.

## Verification evidence

- The locked AAPL revision passed 175 tests; the current main branch suite has 191 tests. Synthetic tests do not need Yahoo.
- Audit of 60 terminal events: equity/cash/holdings reconciliation, terminal fees, and coverage matched.
- Sum of net trade P&L matched account P&L; the largest difference was about 6.26 × 10^-10 USD.
- Cash matched exactly at all three costs; buy and hold had exactly two orders.
- The two seed-42 checkpoints were byte-identical to the source; an audit of 30 RL scenarios confirmed Q/visits remained unchanged and read-only.
- Independent verification of 60 scenarios matched decisions, transitions, Parquet tables, metrics, and diagnostics.
- A clean environment with the relocated exact snapshot also replayed 60/60; the generated report matched byte-for-byte.
- Desktop FinPlot, offscreen seed views, and PNG output rendered successfully in a clean checkout.

Local evidence includes `audit.json`, `clean_environment_verification.json`, verification directories, and the experiment ledger. The saved results can be read or plotted without rerunning the tests.

**Next:** the [project README](../README.md) links to archive restoration and reproduction instructions.
