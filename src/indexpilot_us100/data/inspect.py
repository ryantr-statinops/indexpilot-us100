"""Print a compact quality and descriptive-statistics report for processed bars."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import polars as pl
from statsmodels.tsa.stattools import adfuller


def summarize(path: Path) -> str:
    data = pl.read_parquet(path).sort("date")
    if data.is_empty():
        raise ValueError(f"No rows found in {path}.")

    returns = data.get_column("open_to_open_return").drop_nulls().to_numpy()
    if returns.size < 20:
        raise ValueError("At least 20 non-null returns are required for this summary.")
    adf = adfuller(returns, autolag="AIC", result_object=True)
    adf_stat, adf_pvalue = adf.statistic, adf.pvalue
    pvalue_text = (
        f"{adf_pvalue:.6g}"
        if adf_pvalue > 0
        else "0.0 (floating-point underflow; not exactly zero)"
    )

    lines = [
        f"File: {path}",
        f"Rows: {data.height}",
        f"Date range: {data.get_column('date').min()} to {data.get_column('date').max()}",
        f"Duplicate dates: {data.select(pl.col('date').is_duplicated().sum()).item()}",
        f"Null counts: {data.null_count().row(0, named=True)}",
        "",
        "Synthetic adjusted-open-to-adjusted-open return (per observation, not annualized):",
        f"  count: {returns.size}",
        f"  mean: {np.mean(returns):.8f}",
        f"  standard deviation: {np.std(returns, ddof=1):.8f}",
        f"  1st / 50th / 99th percentiles: {np.quantile(returns, [0.01, 0.5, 0.99])}",
        "",
        "Augmented Dickey-Fuller diagnostic on these returns (not a trading signal):",
        f"  statistic: {adf_stat:.6f}",
        f"  p-value: {pvalue_text}",
        f"  lags used: {adf.lags}; observations used: {adf.nobs}",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("parquet", type=Path, help="Processed Parquet file from indexpilot-fetch")
    args = parser.parse_args()
    print(summarize(args.parquet))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
