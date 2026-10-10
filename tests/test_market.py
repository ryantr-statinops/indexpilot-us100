from datetime import date, timedelta

import numpy as np
import polars as pl
import pytest

from indexpilot_us100.portfolio.market import MarketData, load_market_data


def frame(n=30):
    return pl.DataFrame(
        {
            "date": [date(2020, 1, 1) + timedelta(days=i) for i in range(n)],
            "adj_open": [100.0 + i for i in range(n)],
            "adj_close": [101.0 + i for i in range(n)],
        }
    )


def test_valid(tmp_path):
    path = tmp_path / "input.parquet"
    frame().write_parquet(path)
    market = load_market_data(path)
    assert len(market.dates) == 30
    assert not market.opens.flags.writeable


@pytest.mark.parametrize("bad", [0, -1, None, float("nan"), float("inf")])
def test_bad_price(bad):
    values = [100.0, bad] + [102.0] * 28
    with pytest.raises(ValueError):
        MarketData.from_frame(frame().with_columns(pl.Series("adj_open", values, dtype=pl.Float64)))


def test_dates_and_missing():
    for data in (
        frame().reverse(),
        frame().with_columns(pl.lit(date(2020, 1, 1)).alias("date")),
        frame().drop("adj_open"),
        frame().head(1),
    ):
        with pytest.raises(ValueError):
            MarketData.from_frame(data)


def test_causal_window():
    from indexpilot_us100.portfolio.market import decision_indices, market_features

    market = MarketData.from_frame(frame())
    assert list(decision_indices(market))[0] == 21
    features = market_features(market, 21)
    assert features.return_20 == pytest.approx(121 / 101 - 1)
    assert features.volatility == pytest.approx(
        np.std(np.arange(101.0, 121.0) / np.arange(100.0, 120.0) - 1, ddof=1)
    )
    changed = frame().with_columns(
        pl.when(pl.int_range(pl.len()) >= 21)
        .then(999.0)
        .otherwise(pl.col("adj_open"))
        .alias("adj_open"),
        pl.when(pl.int_range(pl.len()) >= 21)
        .then(777.0)
        .otherwise(pl.col("adj_close"))
        .alias("adj_close"),
    )
    assert market_features(MarketData.from_frame(changed), 21) == features
    with pytest.raises(ValueError, match="warm-up"):
        decision_indices(MarketData.from_frame(frame(22)))
