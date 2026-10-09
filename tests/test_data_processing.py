"""Adjusted prices must be explicit, including across a synthetic split."""
from datetime import date
import polars as pl
import pytest
from indexpilot_us100.data.download import process_source_table


def source():
    return pl.DataFrame({'date':[date(2020,1,2),date(2020,1,3)],'open':[100.,50.], 'high':[101.,51.], 'low':[99.,49.], 'close':[100.,50.], 'adj_close':[50.,50.], 'volume':[1000,2000]})


def test_adjusted_close_is_required():
    with pytest.raises(ValueError,match='adj_close'):
        process_source_table(source().drop('adj_close'))


def test_split_adjustment_keeps_total_return_prices():
    result=process_source_table(source())
    assert result['adj_open'].to_list()==[50.,50.]
    assert result['simple_return'][1]==0
    assert result['open_to_open_return'][1]==0
    assert result['open'].to_list()==[100.,50.]
    assert result['dividends'].to_list()==[0.,0.]


@pytest.mark.parametrize("arguments,ticker", [([], "QQQ"), (["--ticker", "AAPL"], "AAPL"), (["--ticker", "SPY"], "SPY")])
def test_download_cli_ticker_selection(tmp_path, monkeypatch, arguments, ticker):
    from indexpilot_us100.data import download
    calls = []
    def fetch(selected, start, end, output_dir):
        calls.append((selected, start, end, output_dir))
        return {"processed": output_dir / "snapshot.parquet"}
    monkeypatch.setattr(download, "download_daily", fetch)
    assert download.main([*arguments, "--start", "2015-01-01", "--end", "2026-10-06", "--output-dir", str(tmp_path)]) == 0
    assert calls == [(ticker, "2015-01-01", "2026-10-06", tmp_path)]
