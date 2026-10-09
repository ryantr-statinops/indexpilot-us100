# 04 — Simulator, Baselines, and Metrics

## Contents

- [Account and position](#account-and-position)
- [Trades and fees](#trades-and-fees)
- [What happens in one interval](#what-happens-in-one-interval)
- [Reward and risk](#reward-and-risk)
- [Six baselines](#six-baselines)
- [Trades and five metrics](#trades-and-five-metrics)
- [Ledger and outputs](#ledger-and-outputs)

## Account and position

The simulator uses [synthetic adjusted open](03-data.md#adjusted-prices-and-returns). For holdings q, cash C, and price P:

```text
position_value = q * P
equity = C + q * P
exposure = q * P / equity         # only when equity > 0
```

Positive q is long; negative q is short. The simulator uses float64 and fractional units; it has no lot rounding, cash interest, financing, borrow fee, or margin call.

A short sale increases cash but does not create profit by itself. Example without fees: with $10,000 of equity, shorting 100 units at $100 gives $20,000 cash and a −$10,000 position; equity remains $10,000. If the price rises to $110, equity falls to $9,000 and exposure is about −122.22%.

Two instructions have different meanings:

| Instruction | Behavior |
|---|---|
| `TargetExposure(+0.5)` | Set signed position value to 50% of equity after fees |
| `TargetExposure(0)` | Close the position |
| `HoldPosition()` | Keep the same number of units without rebalancing |

Targets must be finite and within [−1, 1]; invalid values are rejected, not clipped. Exposure can drift outside this range while holding; there is no margin intervention while equity remains positive.

Example of a 50% long position without fees: start with $50,000 cash and 500 units at $100. If the price rises to $110, equity becomes $105,000 and exposure is $55,000/$105,000 ≈ 52.38%. Hold keeps the 500 units; a fixed-exposure policy sells units to return to 50%.

## Trades and fees

The default configuration in [stage-2.toml](../configs/stage-2.toml) uses $100,000 initial equity, 10 bps fees, lambda 0, risk window 20, annualization 252, risk-free rate 0, and seed 42.

10 bps = 0.001 = 0.1% of **actual traded notional**. Fees are not charged on total capital every session; spread/slippage are not modeled separately.

For equity E before an order, current position value v = qP, target a, and cost rate k:

```text
x = a * (E - k * abs(x-v))
s = +1 if a*E >= v, otherwise -1
x = a * (E + k*s*v) / (1 + a*k*s)
delta_units = (x-v) / P
fee = k * abs(x-v)
q_after = x / P
cash_after = cash_before - delta_units*P - fee
equity_after = equity_before - fee
```

The target is applied to equity **after paying the fee**, rather than buying a × pre-fee capital and accepting an imprecise final weight.

### Worked example

Start with $100,000 cash, P = $100, target +1, and a 10 bps fee; then let the price rise to $110 and close:

| Quantity | Approximate value |
|---|---:|
| Purchase notional | $99,900.099900 |
| Opening fee | $99.900100 |
| Holdings | 999.000999 units |
| Cash after opening | $0 |
| Exposure after fees | 100% |
| Equity at $110 before closing | $109,890.109890 |
| Closing fee | $109.890110 |
| Final equity | $109,780.219780 |
| Net trade P&L | $9,780.219780 |

If the price stays unchanged, gross P&L is zero but equity still falls by the opening and closing fees.

## What happens in one interval

1. Mark cash and holdings at open i.
2. Create an observation with market features from history before i and account state at the current quote.
3. The policy selects a target or hold instruction.
4. Execute at open i, charge the fee, and update cash and holdings.
5. Hold the position until open i+1 and record gross P&L.
6. Calculate net return/reward and record events and the interval.

The episode starts after sufficient warm-up; all policies use the same eligible interval schedule. No new decision is made at the final open.

At a normal end, the simulator liquidates at the final open and includes the closing fee in the final interval. It does not add a fictitious day to record the fee.

If equity is non-positive, the simulator liquidates at the observed quote and terminates with status `insolvent`. Negative equity is retained to show the debt; exposure is no longer divided by non-positive capital. If short drift leaves positive equity but not enough to pay the closing fee, the position is closed and the episode terminates; the engine adjusts the preceding interval that reached that quote instead of adding a fictitious interval.

## Reward and risk

```text
gross_return = q_after * (next_price-price) / equity_before
cost_fraction = total_interval_fees / equity_before
risk = abs(q_after*price/equity_before) * historical_sample_volatility
reward = gross_return - lambda*risk - cost_fraction
net_return = equity_end/equity_before - 1
```

Risk uses sample volatility of the 20 open returns **available before the decision**. It is a per-interval proxy, not annualized portfolio volatility.

Gross P&L and fees change equity; the risk penalty only affects reward. Do not subtract fees a second time from net return. At lambda 0, reward equals net interval return up to numerical precision; total reward is still not compounded return.

Example: gross return 0.005, cost fraction 0.001, risk 0.01, and lambda 2:

```text
net return = 0.005 - 0.001 = 0.004 = +0.4%
reward = 0.005 - 2*0.01 - 0.001 = -0.016
```

The account makes money during the interval, but reward is negative. This penalty can make the agent prefer flat positions.

## Six baselines

| Policy | Rule |
|---|---|
| `cash` | Always target 0 |
| `buy_hold` | Target +1 at the start of the episode, then `HoldPosition()` |
| `fixed_long_50` | Target +0.5 every session |
| `fixed_short_50` | Target −0.5 every session |
| `sma20_long_flat` | If prior adjusted close > SMA20 before the decision, target +1; otherwise 0 |
| `random_discrete` | NumPy RNG chooses −1/−0.5/0/+0.5/+1 |

SMA20 is a rule specified in advance, not optimized on the test. Random is a sanity check; its RNG resets from the seed for each episode. All policies use the same execution engine and liquidation logic.

## Trades and five metrics

An **order** is an instruction that results in traded notional. A **trade** is a same-direction position episode from opening through flat or reversal. Scaling in/out in the same direction remains part of the same trade; a reversal closes the old trade and opens a new one, allocating fees according to closing/opening notional.

| Metric | Definition |
|---|---|
| Sharpe | Mean excess net interval return / sample standard deviation, ddof=1, multiplied by sqrt(252); annual risk-free rate is compounded to a per-session rate |
| Maximum drawdown | Max(1 − equity/running peak), reported as a positive magnitude over the full event ledger |
| CAGR | (final equity / initial equity)^(365.25 / calendar days) − 1 |
| Profit Factor | Total net P&L of winning trades / absolute total net P&L of losing trades |
| Calmar | CAGR / maximum drawdown |

Opening, rebalance, and closing fees all belong to net trade P&L. After liquidation, total net trade P&L must match final equity minus initial capital. Wins/losses/breakeven use a $10^-8 tolerance to ignore floating-point noise; account P&L is not altered.

Special cases:

- Sharpe with fewer than two returns or standard deviation ≤ 10^-14: undefined.
- Profit Factor with no trades or only breakeven trades: undefined; only wins: +∞; only losses: 0.
- Calmar with zero drawdown and positive CAGR: +∞; zero CAGR and zero drawdown: undefined.
- Insolvent run: Sharpe/CAGR/Calmar are not applicable; MDD may exceed 100%.
- JSON stores null plus `metric_status`; invalid NaN/Infinity values are not serialized as numeric values.

Normalized turnover sums notional/equity_before for orders with positive equity_before. A closing order executed when equity is non-positive still contributes to total notional/fees, but has no valid denominator for normalized turnover.

## Ledger and outputs

```text
summary.csv/json
run_manifest.json
<policy>/
    equity.parquet
    ledger.parquet
    orders.parquet
    trades.parquet
    intervals.parquet
```

The ledger includes initial, execution/hold, mark, and liquidation events. Each event satisfies equity = cash + holdings × price. Cash policies have empty orders/trades tables with complete schemas.

Example of reading saved results without rerunning the policy:

```python
import polars as pl

root = "outputs/stage-2/aapl-default/buy_hold"
print(pl.read_parquet(f"{root}/orders.parquet"))
print(pl.read_parquet(f"{root}/trades.parquet"))
```

MDD in the summary uses the full ledger, including troughs immediately after fees. FinPlot draws daily equity snapshots; a trough after execution that recovers before the next snapshot may not appear as a separate point on the chart.

**Next:** the [project README](../README.md) links to Q-learning and evaluation.
