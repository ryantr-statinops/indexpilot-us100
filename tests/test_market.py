from datetime import date, timedelta
import numpy as np
import polars as pl
import pytest
from indexpilot_us100.portfolio.market import MarketData, load_market_data


def frame(n=30):
    return pl.DataFrame({'date': [date(2020, 1, 1) + timedelta(days=i) for i in range(n)], 'adj_open': [100. + i for i in range(n)], 'adj_close': [101. + i for i in range(n)]})


def test_valid(tmp_path):
    path = tmp_path / 'input.parquet'
    frame().write_parquet(path)
    market = load_market_data(path)
    assert len(market.dates) == 30
    assert not market.opens.flags.writeable


@pytest.mark.parametrize('bad', [0, -1, None, float('nan'), float('inf')])
def test_bad_price(bad):
    values = [100., bad] + [102.] * 28
    with pytest.raises(ValueError):
        MarketData.from_frame(frame().with_columns(pl.Series('adj_open', values, dtype=pl.Float64)))


def test_dates_and_missing():
    for data in (frame().reverse(), frame().with_columns(pl.lit(date(2020, 1, 1)).alias('date')), frame().drop('adj_open'), frame().head(1)):
        with pytest.raises(ValueError):
            MarketData.from_frame(data)
