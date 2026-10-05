"""Financial scorecard conventions and explicit undefined-value states."""
from dataclasses import dataclass
import numpy as np
from indexpilot_us100.portfolio.simulator import SimulationResult


@dataclass(frozen=True)
class Metric:
    value: float | None
    status: str = 'finite'


@dataclass
class MetricsReport:
    summary: dict
    metrics: dict[str, Metric]

    def row(self):
        row = dict(self.summary)
        for name, metric in self.metrics.items():
            row[name] = metric.value
            row[name + '_status'] = metric.status
        return row


def drawdown_curve(equities) -> np.ndarray:
    values = np.asarray(equities, dtype=np.float64)
    if values.ndim != 1 or not len(values) or not np.all(np.isfinite(values)) or values[0] <= 0:
        raise ValueError('Equity curve must be finite, nonempty and start positive')
    return 1 - values / np.maximum.accumulate(values)


def compute_metrics(result: SimulationResult) -> MetricsReport:
    first, last = result.equity[0], result.equity[-1]
    equity_values = [row['equity'] for row in result.ledger]
    pnl = last['equity'] - first['equity']
    trade_values = np.array([row['net_pnl'] for row in result.trades], dtype=float)
    summary = dict(baseline=result.baseline, status=result.status, start_date=first['date'].isoformat(), end_date=last['date'].isoformat(), interval_count=len(result.intervals), initial_equity=first['equity'], final_equity=last['equity'], net_pnl=pnl, net_return=last['equity'] / first['equity'] - 1, total_fees=sum(row['fee'] for row in result.orders), traded_notional=sum(row['traded_notional'] for row in result.orders), normalized_turnover=sum(row['traded_notional'] / row['equity_before'] for row in result.orders if row['equity_before'] > 0), order_count=len(result.orders), trade_count=len(result.trades), wins=int(np.sum(trade_values > 1e-8)), losses=int(np.sum(trade_values < -1e-8)), breakeven=int(np.sum(np.abs(trade_values) <= 1e-8)), total_reward=sum(row['reward'] for row in result.intervals), seed=result.config.seed)
    return MetricsReport(summary, {'max_drawdown': Metric(float(np.max(drawdown_curve(equity_values))))})
