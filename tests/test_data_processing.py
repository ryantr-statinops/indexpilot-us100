"""Adjusted prices must be explicit, including across a synthetic split."""

from datetime import date

import polars as pl
import pytest

from indexpilot_us100.data.download import process_source_table


def source():
    return pl.DataFrame(
        {
            "date": [date(2020, 1, 2), date(2020, 1, 3)],
            "open": [100.0, 50.0],
            "high": [101.0, 51.0],
            "low": [99.0, 49.0],
            "close": [100.0, 50.0],
            "adj_close": [50.0, 50.0],
            "volume": [1000, 2000],
        }
    )


def test_adjusted_close_is_required():
    with pytest.raises(ValueError, match="adj_close"):
        process_source_table(source().drop("adj_close"))


def test_split_adjustment_keeps_total_return_prices():
    result = process_source_table(source())
    assert result["adj_open"].to_list() == [50.0, 50.0]
    assert result["simple_return"][1] == 0
    assert result["open_to_open_return"][1] == 0
    assert result["open"].to_list() == [100.0, 50.0]
    assert result["dividends"].to_list() == [0.0, 0.0]


@pytest.mark.parametrize(
    "arguments,ticker", [([], "QQQ"), (["--ticker", "AAPL"], "AAPL"), (["--ticker", "SPY"], "SPY")]
)
def test_download_cli_ticker_selection(tmp_path, monkeypatch, arguments, ticker):
    from indexpilot_us100.data import download

    calls = []

    def fetch(selected, start, end, output_dir):
        calls.append((selected, start, end, output_dir))
        return {"processed": output_dir / "snapshot.parquet"}

    monkeypatch.setattr(download, "download_daily", fetch)
    assert (
        download.main(
            [
                *arguments,
                "--start",
                "2015-01-01",
                "--end",
                "2026-10-06",
                "--output-dir",
                str(tmp_path),
            ]
        )
        == 0
    )
    assert calls == [(ticker, "2015-01-01", "2026-10-06", tmp_path)]


def test_download_manifest_describes_single_asset_snapshot(tmp_path, monkeypatch):
    import json

    from indexpilot_us100.data import download

    monkeypatch.setattr(download.yf, "download", lambda **kwargs: object())
    monkeypatch.setattr(
        download, "normalize_download", lambda frame: process_source_table(source())
    )
    paths = download.download_daily("QQQ", "2020-01-01", "2020-01-04", tmp_path)
    manifest = json.loads(paths["manifest"].read_text())
    assert manifest["ticker"] == "QQQ"
    assert "Yahoo Finance" in manifest["provider"]
    assert "single-asset" in manifest["caveat"]
    assert "constituent" not in manifest["caveat"]
    assert "Adj Close / Close" in manifest["price_convention"]
    assert set(manifest["files"]) == {paths["raw"].name, paths["processed"].name}


def test_normalize_yahoo_multilevel_columns():
    import pandas as pd

    from indexpilot_us100.data.download import normalize_download

    frame = pd.DataFrame(
        [[100.0, 101.0, 99.0, 100.0, 50.0, 1000], [50.0, 51.0, 49.0, 50.0, 50.0, 2000]],
        index=pd.to_datetime(["2020-01-02", "2020-01-03"]),
        columns=pd.MultiIndex.from_tuples(
            [
                ("Open", "QQQ"),
                ("High", "QQQ"),
                ("Low", "QQQ"),
                ("Close", "QQQ"),
                ("Adj Close", "QQQ"),
                ("Volume", "QQQ"),
            ]
        ),
    )
    original = frame.copy(deep=True)
    result = normalize_download(frame)
    assert result.equals(process_source_table(source()))
    pd.testing.assert_frame_equal(frame, original)


def test_archived_csv_rebuild_matches_processed_snapshot(tmp_path):
    from indexpilot_us100.data.download import process_raw_csv

    raw = tmp_path / "snapshot_raw.csv"
    source().write_csv(raw)
    output = tmp_path / "restored" / "snapshot_processed.parquet"
    assert process_raw_csv(raw, output) == output
    assert pl.read_parquet(output).equals(process_source_table(source()))
