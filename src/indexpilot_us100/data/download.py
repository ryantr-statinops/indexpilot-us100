"""Download daily Yahoo Finance bars and create a reproducible local snapshot."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import polars as pl
import yfinance as yf


def _column_name(column: Any) -> str:
    """Flatten yfinance's version-dependent single-ticker column labels."""
    parts = column if isinstance(column, tuple) else (column,)
    known = {
        "open": "open",
        "high": "high",
        "low": "low",
        "close": "close",
        "adj close": "adj_close",
        "volume": "volume",
        "dividends": "dividends",
        "stock splits": "stock_splits",
        "capital gains": "capital_gains",
    }
    for part in parts:
        name = str(part).strip().lower()
        if name in known:
            return known[name]
    return str(parts[-1]).strip().lower().replace(" ", "_")


def _normalize_source_columns(data: pl.DataFrame) -> pl.DataFrame:
    if data.is_empty():
        raise ValueError("Source data contains no rows.")
    if "date" not in data.columns:
        date_candidates = [name for name in data.columns if name.lower() in {"date", "datetime"}]
        if not date_candidates:
            raise ValueError(f"Could not identify a date column in {data.columns!r}.")
        data = data.rename({date_candidates[0]: "date"})
    required = {"open", "high", "low", "close", "adj_close", "volume"}
    missing = sorted(required.difference(data.columns))
    if missing:
        raise ValueError(f"Downloaded data is missing required columns: {missing}.")

    for optional in ("dividends", "stock_splits", "capital_gains"):
        if optional not in data.columns:
            data = data.with_columns(pl.lit(0.0).alias(optional))

    return data


def _derive_adjusted_returns(data: pl.DataFrame) -> pl.DataFrame:
    data = data.with_columns(
        (pl.col("open") * pl.col("adj_close") / pl.col("close")).alias("adj_open"),
        pl.col("adj_close").pct_change().alias("simple_return"),
        (pl.col("adj_close").log() - pl.col("adj_close").shift(1).log()).alias("log_return"),
        (pl.col("open") * pl.col("adj_close") / pl.col("close")).pct_change().alias("open_to_open_return"),
    )
    return data



def process_source_table(data: pl.DataFrame) -> pl.DataFrame:
    """Validate the normalized source columns and add adjusted-close returns."""
    data = _normalize_source_columns(data)

    data = (
        data.with_columns(pl.col("date").cast(pl.Date, strict=False))
        .select(
            "date", "open", "high", "low", "close", "adj_close", "volume",
            "dividends", "stock_splits", "capital_gains",
        )
        .sort("date")
    )
    if data.get_column("date").null_count():
        raise ValueError("Some rows have invalid dates.")

    return _derive_adjusted_returns(data)


def normalize_download(frame: Any) -> pl.DataFrame:
    """Normalize a yfinance DataFrame to a flat Polars daily-bars table."""
    if frame is None or frame.empty:
        raise ValueError("Yahoo Finance returned no rows for this ticker/date range.")

    pandas_frame = frame.copy()
    pandas_frame.columns = [_column_name(column) for column in pandas_frame.columns]
    pandas_frame.index.name = "date"
    records = pandas_frame.reset_index().to_dict(orient="records")
    data = pl.DataFrame(records)
    data = data.rename({name: name.lower().replace(" ", "_") for name in data.columns})
    return process_source_table(data)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _download_source(ticker: str, start: str, end: str):
    return yf.download(
        tickers=ticker,
        start=start,
        end=end,
        interval="1d",
        auto_adjust=False,
        actions=True,
        progress=False,
        threads=False,
        multi_level_index=False,
    )


def _snapshot_quality(normalized: pl.DataFrame) -> dict[str, Any]:
    duplicate_dates = normalized.select(pl.col("date").is_duplicated().sum()).item()
    invalid_price_rows = normalized.filter(
        pl.any_horizontal(
            [
                pl.col(name).is_null() | (pl.col(name) <= 0)
                for name in ("open", "high", "low", "close", "adj_close", "adj_open")
            ]
        )
    ).height
    null_counts = {
        name: count
        for name, count in normalized.null_count().row(0, named=True).items()
        if count
    }
    return {
        "duplicate_date_rows": duplicate_dates,
        "rows_with_null_or_nonpositive_prices": invalid_price_rows,
        "null_counts_processed": null_counts,
    }


def _snapshot_manifest(ticker: str, start: str, end: str, normalized: pl.DataFrame, raw_path: Path, processed_path: Path, quality: dict[str, Any]) -> dict[str, Any]:
    return {
        "provider": "Yahoo Finance via yfinance",
        "ticker": ticker,
        "interval": "1d",
        "date_semantics": "U.S. exchange session date labels; daily bars have no intraday timestamp timezone.",
        "start_inclusive": start,
        "end_exclusive": end,
        "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
        "yfinance_version": yf.__version__,
        "price_convention": (
            "Normalized source response saved with auto_adjust=False. Processed simple_return and log_return "
            "use Adj Close. adj_open and open_to_open_return use the synthetic total-return factor "
            "Adj Close / Close applied to Open; source OHLC remain unadjusted."
        ),
        "rows": normalized.height,
        "first_date": str(normalized.get_column("date").min()),
        "last_date": str(normalized.get_column("date").max()),
        "duplicate_date_rows": quality["duplicate_date_rows"],
        "rows_with_null_or_nonpositive_prices": quality["rows_with_null_or_nonpositive_prices"],
        "null_counts_processed": quality["null_counts_processed"],
        "files": {
            raw_path.name: {"sha256": _sha256(raw_path)},
            processed_path.name: {"sha256": _sha256(processed_path)},
        },
        "caveat": (
            "yfinance is an unofficial access route to Yahoo Finance data. This snapshot is for "
            "single-asset research/education using synthetic adjusted prices, "
            "and should not be treated as live-trading data."
        ),
    }


def _write_snapshot_files(normalized: pl.DataFrame, raw_path: Path, processed_path: Path) -> None:
    # Persist the normalized source response including adjusted close and corporate actions.
    # The processed file below adds derived returns and uses Polars' typed Parquet output.
    normalized.drop("adj_open", "simple_return", "log_return", "open_to_open_return").write_csv(raw_path)
    normalized.write_parquet(processed_path)



def _write_snapshot_manifest(manifest_path: Path, manifest: dict[str, Any]) -> None:
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def download_daily(ticker: str, start: str, end: str, output_dir: Path) -> dict[str, Path]:
    """Download a ticker, persist source and processed data, and write metadata.

    ``start`` is inclusive and ``end`` is exclusive, following yfinance's API.
    """
    ticker = ticker.strip().upper()
    if not ticker:
        raise ValueError("Ticker must not be blank.")
    output_dir.mkdir(parents=True, exist_ok=True)

    frame = _download_source(ticker, start, end)
    normalized = normalize_download(frame)

    prefix = f"{ticker.lower()}_daily_{start}_to_{end}"
    raw_path = output_dir / f"{prefix}_raw.csv"
    processed_path = output_dir / f"{prefix}_processed.parquet"
    manifest_path = output_dir / f"{prefix}_manifest.json"

    _write_snapshot_files(normalized, raw_path, processed_path)
    quality = _snapshot_quality(normalized)
    manifest = _snapshot_manifest(ticker, start, end, normalized, raw_path, processed_path, quality)
    _write_snapshot_manifest(manifest_path, manifest)
    return {"raw": raw_path, "processed": processed_path, "manifest": manifest_path}


def process_raw_csv(raw_path: Path, processed_path: Path) -> Path:
    """Rebuild a processed Parquet file from the archived normalized source CSV."""
    source = pl.read_csv(raw_path, try_parse_dates=True)
    processed = process_source_table(source)
    processed_path.parent.mkdir(parents=True, exist_ok=True)
    processed.write_parquet(processed_path)
    return processed_path


def process_main(argv: list[str] | None = None) -> int:
    """CLI entry point for reprocessing an archived raw CSV snapshot."""
    parser = argparse.ArgumentParser(description="Reprocess an archived normalized Yahoo Finance CSV")
    parser.add_argument("raw_csv", type=Path, help="Raw CSV written by indexpilot-fetch")
    parser.add_argument("--output", type=Path, help="Output Parquet path")
    args = parser.parse_args(argv)
    output_path = args.output or args.raw_csv.with_name(
        args.raw_csv.name.replace("_raw.csv", "_processed.parquet")
    )
    try:
        process_raw_csv(args.raw_csv, output_path)
    except Exception as error:
        print(f"Data processing failed: {error}", file=sys.stderr)
        return 1
    print(f"processed: {output_path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ticker", default="QQQ", help="Yahoo Finance ticker (default: QQQ)")
    parser.add_argument("--start", default="2015-01-01", help="Inclusive date, YYYY-MM-DD")
    parser.add_argument(
        "--end",
        default=datetime.now(timezone.utc).date().isoformat(),
        help="Exclusive date, YYYY-MM-DD (default: current UTC date)",
    )
    parser.add_argument("--output-dir", type=Path, default=Path("data"))
    args = parser.parse_args(argv)
    try:
        paths = download_daily(args.ticker, args.start, args.end, args.output_dir)
    except Exception as error:
        print(f"Data download failed: {error}", file=sys.stderr)
        return 1
    for kind, path in paths.items():
        print(f"{kind}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
