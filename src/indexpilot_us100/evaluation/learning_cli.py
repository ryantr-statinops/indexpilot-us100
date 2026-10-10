"""Train tabular Q policies; compare on validation and reserve the test period."""

import argparse
import tomllib

import polars as pl

from indexpilot_us100.agents.config import load_learning_config
from indexpilot_us100.agents.training import run_experiments
from indexpilot_us100.metrics import compute_metrics
from indexpilot_us100.portfolio.market import load_market_data

from .cli import comparison_table
from .learning_export import export_learning, validate_learning_destination


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)
    try:
        output = validate_learning_destination(args.data, args.output_dir, args.overwrite)
        simulation, learning = load_learning_config(args.config)
        market = load_market_data(args.data)
        progress = None if args.quiet else lambda message: print(message, flush=True)
        experiments, selection = run_experiments(market, simulation, learning, progress)
        export_learning(
            experiments, selection, simulation, learning, args.data, output, args.overwrite
        )
    except (
        OSError,
        ValueError,
        TypeError,
        tomllib.TOMLDecodeError,
        pl.exceptions.PolarsError,
    ) as error:
        parser.error(str(error))
    for experiment in experiments:
        print(f"\nGreedy validation — lambda={experiment.risk_lambda:g}")
        print(
            comparison_table(
                [
                    compute_metrics(result)
                    for result in [*experiment.baselines, experiment.validation.result]
                ]
            )
        )
    print(
        f"\nSelection: lambda={selection['selected_lambda']:g}; {selection['status']} (validation Sharpe only)"
    )
    print(f"Test period from {learning.test_start} was not evaluated.")
    print(f"Artifacts: {args.output_dir}")
    return 0
