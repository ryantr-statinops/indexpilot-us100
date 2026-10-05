"""Optional FinPlot viewer for persisted equity and drawdown."""
import argparse
import json
import os
from pathlib import Path
import sys
import numpy as np
import polars as pl


def load_chart_series(run_dir: str | Path):
    root = Path(run_dir)
    manifest = json.loads((root / 'run_manifest.json').read_text())
    if manifest.get('artifact_type') != 'indexpilot-stage-2':
        raise ValueError('Expected a Stage 2 run manifest')
    series = []
    for baseline in manifest['baselines']:
        name = baseline['name']
        if not name or not all(ch.isalnum() or ch in '_-' for ch in name):
            raise ValueError('Unsafe baseline name')
        table = pl.read_parquet(root / name / 'equity.parquet')
        if not {'date', 'equity', 'drawdown'} <= set(table.columns):
            raise ValueError(f'Missing chart columns for {name}')
        # Exchange session labels, plotted as UTC midnight without intraday meaning.
        seconds = table['date'].cast(pl.Datetime('us')).cast(pl.Int64).to_numpy().astype(float) / 1_000_000
        equity = table['equity'].to_numpy()
        drawdown = table['drawdown'].to_numpy() * 100
        if len(seconds) < 2 or not np.all(np.isfinite(seconds)) or np.any(np.diff(seconds) <= 0) or not np.all(np.isfinite(equity)) or not np.all(np.isfinite(drawdown)):
            raise ValueError(f'Invalid chart series for {name}')
        series.append(dict(name=name, status=baseline['status'], times=seconds, equity=equity, drawdown=drawdown))
    if not series:
        raise ValueError('No chart series')
    return series


def create_chart(series):
    try:
        import finplot as fplt
    except ImportError as error:
        raise RuntimeError('Install chart dependencies with: uv sync --extra dev --extra charts') from error
    fplt.legend_text_color = '#222222'
    fplt.legend_fill_color = '#ffffffe6'
    axes = fplt.create_plot('Stage 2 — baseline equity and drawdown (%)', rows=2, maximize=False)
    axes[0].setLabel('left', 'Equity', units='USD')
    axes[1].setLabel('left', 'Drawdown', units='%')
    for number, item in enumerate(series):
        label = item['name'] + (' [insolvent]' if item['status'] == 'insolvent' else '')
        style = '--' if item['name'] == 'random_discrete' else '-'
        fplt.plot(item['times'], item['equity'], ax=axes[0], color=number, legend=label, style=style)
        fplt.plot(item['times'], item['drawdown'], ax=axes[1], color=number, legend=label, style=style)
    return fplt, axes


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', required=True)
    args = parser.parse_args(argv)
    try:
        series = load_chart_series(args.run_dir)
        if sys.platform.startswith('linux') and not (os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY') or os.environ.get('QT_QPA_PLATFORM') == 'offscreen'):
            raise RuntimeError('FinPlot needs a desktop display; simulation artifacts remain available.')
        fplt, _ = create_chart(series)
    except (OSError, ValueError, RuntimeError, pl.exceptions.PolarsError) as error:
        parser.error(str(error))
    fplt.show()
    return 0
