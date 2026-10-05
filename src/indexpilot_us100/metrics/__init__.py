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
    metrics = {'max_drawdown': Metric(float(np.max(drawdown_curve(equity_values))))}
    if result.status == 'insolvent':
        metrics.update(sharpe=Metric(None, 'not_applicable'), cagr=Metric(None, 'not_applicable'))
    else:
        metrics['sharpe'] = sharpe_ratio([row['net_return'] for row in result.intervals], result.config.annualization, result.config.risk_free_annual)
        metrics['cagr'] = compound_growth(first['equity'], last['equity'], (last['date'] - first['date']).days)
    metrics['profit_factor'] = profit_factor(trade_values)
    metrics['calmar'] = Metric(None, 'not_applicable') if result.status == 'insolvent' else calmar_ratio(metrics['cagr'], metrics['max_drawdown'].value)
    return MetricsReport(summary, metrics)


def sharpe_ratio(returns, annualization=252, risk_free_annual=0.) -> Metric:
    values = np.asarray(returns, dtype=np.float64)
    if values.ndim != 1 or len(values) < 2 or not np.all(np.isfinite(values)):
        return Metric(None, 'undefined')
    if annualization <= 0 or not np.isfinite(risk_free_annual) or risk_free_annual <= -1:
        raise ValueError('Invalid annualization or risk-free rate')
    volatility = float(np.std(values, ddof=1))
    if volatility <= 1e-14:
        return Metric(None, 'undefined')
    daily_rf = np.expm1(np.log1p(risk_free_annual) / annualization)
    value = float((np.mean(values) - daily_rf) / volatility * np.sqrt(annualization))
    return Metric(value) if np.isfinite(value) else Metric(None, 'undefined')


def compound_growth(initial, final, elapsed_days) -> Metric:
    if initial <= 0 or final <= 0 or elapsed_days <= 0:
        return Metric(None, 'undefined')
    with np.errstate(over='ignore', invalid='ignore'):
        value = float(np.expm1(np.log(final / initial) * 365.25 / elapsed_days))
    return Metric(value) if np.isfinite(value) else Metric(None, 'undefined')


def profit_factor(trade_pnls) -> Metric:
    values = np.asarray(trade_pnls, dtype=np.float64)
    if values.ndim != 1 or not np.all(np.isfinite(values)):
        raise ValueError('Trade P&Ls must be finite')
    gains = float(np.sum(values[values > 1e-8]))
    losses = float(-np.sum(values[values < -1e-8]))
    if losses:
        return Metric(gains / losses)
    return Metric(None, 'positive_infinity' if gains else 'undefined')


def calmar_ratio(cagr: Metric, max_drawdown: float) -> Metric:
    if cagr.value is None:
        return Metric(None, cagr.status)
    if max_drawdown == 0:
        return Metric(None, 'positive_infinity' if cagr.value > 0 else 'undefined')
    return Metric(cagr.value / max_drawdown)
