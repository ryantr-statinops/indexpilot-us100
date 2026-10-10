"""Prepare, evaluate and independently verify the frozen final experiment."""

import argparse
from pathlib import Path

import polars as pl

from .config import EvaluationConfig
from .history import ExperimentLedger
from .protocol import prepare_protocol
from .workflow import run_evaluation, verify_evaluation


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare")
    for field in ("data", "source-run", "config", "output-dir"):
        prepare.add_argument("--" + field, required=True)
    prepare.add_argument("--reason")
    for command in ("run", "verify", "report"):
        child = commands.add_parser(command)
        child.add_argument("--protocol-dir", required=True)
        child.add_argument("--data", help="Relocated exact snapshot; SHA256 must match")
        if command == "report":
            child.add_argument("--output")
    args = parser.parse_args(argv)
    try:
        if args.command == "prepare":
            history = ExperimentLedger(Path(args.output_dir).parent / "experiment-ledger.jsonl")
            history.require_new_reason(args.reason)
            config = EvaluationConfig.from_toml(args.config)
            protocol = prepare_protocol(
                args.data,
                args.source_run,
                config,
                args.output_dir,
                lambda message: print(message, flush=True),
            )
            history.append(
                "prepared",
                protocol["protocol_id"],
                output_directory=str(Path(args.output_dir).resolve()),
                reason=args.reason,
                input_sha256=protocol["input_sha256"],
            )
            print("Frozen protocol:", protocol["protocol_id"])
        elif args.command == "run":
            manifest = run_evaluation(
                args.protocol_dir, args.data, lambda scenario: print(scenario, flush=True)
            )
            print("Completed:", len(manifest["scenarios"]), "scenarios")
            print(
                pl.read_csv(Path(args.protocol_dir) / "primary_summary.csv").select(
                    "policy",
                    "risk_lambda",
                    "net_return",
                    "sharpe",
                    "max_drawdown",
                    "trade_count",
                    "active_intervals",
                )
            )
        elif args.command == "report":
            from .report import generate_report

            print("Report:", generate_report(args.protocol_dir, args.output))
        else:
            replay = verify_evaluation(
                args.protocol_dir, args.data, lambda scenario: print("verify", scenario, flush=True)
            )
            print("Verified replay:", replay)
    except (OSError, ValueError, KeyError, pl.exceptions.PolarsError) as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
