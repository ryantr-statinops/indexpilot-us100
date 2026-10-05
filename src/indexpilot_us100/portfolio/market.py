"""Validate simulation input without filling or reordering observations."""
from dataclasses import dataclass
from datetime import date
from pathlib import Path
import numpy as np
import polars as pl


@dataclass(frozen=True)
class MarketData:
    dates: tuple[date, ...]
    opens: np.ndarray
    closes: np.ndarray
    warnings: tuple[str, ...] = ()

    @classmethod
    def from_frame(cls, frame: pl.DataFrame):
        required = {'date', 'adj_open', 'adj_close'}
        if not required <= set(frame.columns):
            raise ValueError(f'Missing required columns: {sorted(required - set(frame.columns))}')
        if frame.height < 2:
            raise ValueError('Need at least two market rows')
        if frame['date'].dtype != pl.Date:
            raise ValueError('date must use the Date type (daily session labels)')
        dates = tuple(frame['date'].to_list())
        if any(value is None for value in dates):
            raise ValueError('Null dates are not allowed')
        if any(b <= a for a, b in zip(dates, dates[1:])):
            raise ValueError('Dates must be unique and strictly increasing')
        arrays = []
        for name in ('adj_open', 'adj_close'):
            try:
                values = frame[name].cast(pl.Float64, strict=True).to_numpy().copy()
            except (pl.exceptions.PolarsError, TypeError) as error:
                raise ValueError(f'{name} must be numeric') from error
            if not np.all(np.isfinite(values) & (values > 0)):
                raise ValueError(f'{name} must contain finite positive prices without nulls')
            values.setflags(write=False)
            arrays.append(values)
        gaps = sum((b - a).days > 4 for a, b in zip(dates, dates[1:]))
        warnings = ('Exchange calendar completeness is not verified.',)
        if gaps:
            warnings += (f'{gaps} date gaps exceed four calendar days; inspect source coverage.',)
        return cls(dates, *arrays, warnings)


def load_market_data(path: str | Path) -> MarketData:
    return MarketData.from_frame(pl.read_parquet(path))


@dataclass(frozen=True)
class MarketFeatures:
    return_1: float
    return_5: float
    return_20: float
    volatility: float
    prior_close: float
    sma20: float


def decision_indices(market: MarketData, risk_window: int = 20) -> range:
    if type(risk_window) is not int or risk_window < 2:
        raise ValueError('risk_window must be an integer >= 2')
    start = max(20, risk_window) + 1
    if start >= len(market.dates) - 1:
        raise ValueError('Insufficient warm-up or no open-to-open holding interval')
    return range(start, len(market.dates) - 1)


def market_features(market: MarketData, index: int, risk_window: int = 20) -> MarketFeatures:
    if index not in decision_indices(market, risk_window):
        raise ValueError('Index is outside the eligible decision window')
    closes = market.closes
    # Ends at previous open, deliberately excluding the current-open return.
    returns = market.opens[index-risk_window:index] / market.opens[index-risk_window-1:index-1] - 1
    return MarketFeatures(
        *(float(closes[index-1] / closes[index-1-lag] - 1) for lag in (1, 5, 20)),
        float(np.std(returns, ddof=1)), float(closes[index-1]),
        float(np.mean(closes[index-20:index])),
    )
