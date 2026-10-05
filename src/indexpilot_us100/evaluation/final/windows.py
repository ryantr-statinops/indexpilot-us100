"""Causal test slicing with account reset at the first eligible test open."""
from bisect import bisect_left,bisect_right
from datetime import date
from indexpilot_us100.portfolio.market import MarketData,decision_indices


def build_test_segment(market,config,simulation):
    start,end=date.fromisoformat(config.test_start),date.fromisoformat(config.test_end)
    if end>market.dates[-1]: raise ValueError('Snapshot does not cover the declared test end')
    first=bisect_left(market.dates,start)
    stop=bisect_right(market.dates,end)
    warmup=max(20,simulation.risk_window)+1
    if first<warmup or stop-first<2:
        raise ValueError('Test needs prior warm-up and at least two in-range opens')
    result=MarketData(market.dates[first-warmup:stop],market.opens[first-warmup:stop],market.closes[first-warmup:stop],market.warnings)
    decision_indices(result,simulation.risk_window)
    return result
