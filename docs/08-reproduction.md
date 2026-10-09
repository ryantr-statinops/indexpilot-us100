# 08 — Reproducing the Experiment

## Contents

- [Requirements](#requirements)
- [Restore the archive in a clean checkout](#restore-the-archive-in-a-clean-checkout)
- [Replay and verify](#replay-and-verify)
- [Generate a report and PNG charts from artifacts](#generate-a-report-and-png-charts-from-artifacts)
- [Prepare a new protocol from source](#prepare-a-new-protocol-from-source)
- [Troubleshooting](#troubleshooting)

## Requirements

Exact reproduction requires **the same bytes of the locked snapshot, models, and configuration**. The repository contains only code/configuration/documentation; data, checkpoints, and detailed outputs are Git-ignored.

| Input | Needed for |
|---|---|
| Repository and `uv.lock` compatible with the protocol | Running the evaluator/verification |
| Exact processed Parquet | Running or recomputing verification |
| `protocol.json`, `frozen_models`, and `preparation` | Loading/checking the frozen inventory and provenance |
| Saved runs/summaries/manifest | Reusing a completed run, comparing verification, report/chart |
| Source learning run | Preparing the inventory again from source |
| Experiment ledger | Retaining the preparation/evaluation history |

The current local archive is `outputs/stage-4/aapl-reproduction.tar.gz`, about 16 MB. Its manifest is `outputs/stage-4/reproduction_archive_manifest.json`.

```text
Archive SHA256:
4a47e5d16e617a14328b37be2869cc2e7825b803f14bcfba4ff8c63e68789889

Dataset SHA256:
042605225d9f9dc91ac983ceb13079f09077a569bd485dd06774263f994db3cc

Protocol ID:
5fbce9eb3c97815487c57b7eaca4502390562e37ed062609d72c87ba189ec18b

Calculation revision:
b6c550da754fec519d14b7a0a9610a219b303904
```

The archive is on the machine that ran the experiment and is not downloaded with a Git clone. Transfer the archive separately in accordance with data-use permissions. Do not treat a fresh Yahoo download as an exact replacement if its hash differs.

## Restore the archive in a clean checkout

Example, with the archive stored separately on the machine:

```bash
git clone https://github.com/ryantr-statinops/indexpilot-us100.git indexpilot-us100-frozen
cd indexpilot-us100-frozen
git checkout --detach b6c550d
uv sync --python 3.11.16 --frozen --extra dev --extra charts

sha256sum /absolute/path/aapl-reproduction.tar.gz
tar -xzf /absolute/path/aapl-reproduction.tar.gz \
  data/raw/aapl_daily_2015-01-01_to_2026-10-06_processed.parquet \
  outputs/stage-3/aapl-default \
  outputs/stage-4/aapl-frozen \
  outputs/stage-4/experiment-ledger.jsonl
```

Replace the archive path with the actual file location. The listed archive members are the experiment inputs/artifacts. Use a new checkout so you do not overwrite another local experiment.

The code revision used when the protocol was locked is `b6c550d`. Main now includes Python hardening and refactoring, so exact `run`/`verify` of the old archive requires this checkout. Preserve the protocol/model/data hashes; do not update the old fingerprint to bypass an error. Read the current documentation from main and run replay commands in the separate frozen checkout. Report/chart commands can read the old artifacts on main as well.

Documentation-only revisions remain compatible; changes to code, including formatting/types/report helpers, are detected because the fingerprint includes the entire Python package.

## Replay and verify

When moving to another machine, the absolute `input_file` path in the protocol may point to the old machine. Use `--data` to provide the restored file; its SHA256 must still match:

```bash
uv run indexpilot-evaluate run \
  --protocol-dir outputs/stage-4/aapl-frozen \
  --data data/raw/aapl_daily_2015-01-01_to_2026-10-06_processed.parquet

uv run indexpilot-evaluate verify \
  --protocol-dir outputs/stage-4/aapl-frozen \
  --data data/raw/aapl_daily_2015-01-01_to_2026-10-06_processed.parquet
```

For a completed archive, `run` checks integrity and returns the artifacts; `verify` actually recomputes 60 scenarios in a new `verification-*` directory and compares them with the saved results. You can run `run` to resume an incomplete experiment; completed scenarios are hash-checked before reuse.

Verification compares decisions, RL transitions, accounting Parquet files, metrics/diagnostics, and summary files. Exporter timestamps/Git fields are not part of the numerical comparison, but provenance files remain in the completion hashes. A verified event is appended to the ledger.

Fixture tests can run independently of the snapshot/Yahoo:

```bash
uv run pytest -q
```

The locked AAPL revision has 175 tests and an independent 60-scenario replay in a clean virtual environment. The hardened main suite has 191 tests; fixtures cover the adjusted-close requirement, inputs changing during preparation, atomic manifest/recovery, December insolvency coverage, and report composition. The aggregate matrix before and after refactoring retained the same summaries, accounting tables, and Q/visits; the generated report remained byte-identical. AAPL was independently verified again, 60/60, in a separate checkout at `b6c550d` after hardening.

## Generate a report and PNG charts from artifacts

These commands read saved results; they do not train or reevaluate:

```bash
uv run indexpilot-evaluate report --protocol-dir outputs/stage-4/aapl-frozen

uv run indexpilot-chart --run-dir outputs/stage-4/aapl-frozen \
  --save-png outputs/stage-4/aapl-frozen/figures/primary.png

QT_QPA_PLATFORM=offscreen uv run indexpilot-chart \
  --run-dir outputs/stage-4/aapl-frozen --seeds --risk-lambda 2 --cost-bps 10 \
  --save-png outputs/stage-4/aapl-frozen/figures/primary-seeds.png
```

By default, the report is `report.md` in the run directory. Optional `--output` selects another destination; the [results chapter](07-results.md) is a separate editorial interpretation, while the generated report is stored locally.

The chart has two panels for equity/drawdown; `--cost-bps` selects a declared cost, while `--seeds` and `--risk-lambda` select all RL seeds for one lambda. `--save-png` renders with Qt and then closes the window. Offscreen rendering works without a desktop display; the core evaluator does not need the `charts` extra.

You can read tables directly:

```python
import polars as pl

root = "outputs/stage-4/aapl-frozen"
print(pl.read_csv(f"{root}/primary_summary.csv"))
print(pl.read_csv(f"{root}/paired_comparison.csv"))
```

## Prepare a new protocol from source

To create a protocol with the hardened code, use a **separate main checkout**, restore the exact snapshot/source learning run and ledger, select a different output directory, and record a reason after a test has been completed. The following commands run on main:

```bash
uv run indexpilot-evaluate prepare \
  --data data/raw/aapl_daily_2015-01-01_to_2026-10-06_processed.parquet \
  --source-run outputs/stage-3/aapl-default \
  --config configs/stage-4.toml \
  --output-dir outputs/stage-4/aapl-reprepared \
  --reason "Rebuild inventory from archived training inputs"
```

`prepare` copies the two seed-42 checkpoints and trains eight additional models on the original training segment; it does not evaluate the test. The protocol ID changes because the preparation timestamp is different. To replay the **old experiment**, use the archived inventory and old protocol instead of preparing again.

The raw CSV can also be reprocessed to learn the pipeline, but exact reproduction requires a Parquet file with the hash of the locked snapshot. Do not bypass a hash mismatch.

## Troubleshooting

| Problem | Resolution |
|---|---|
| Parquet/models/artifacts missing after clone | Restore the archived inputs; review the requirements first |
| Data hash changed | Find the snapshot with the recorded hash; use `--data` to change the path if the bytes match |
| Model/log/source hash changed | Restore the original archive and compare with its manifest |
| Code or dependency lock changed | The old AAPL archive uses `b6c550d`; hardened main requires a new protocol; do not edit the old fingerprint |
| Numerical runtime differs | Create a separate environment with Python 3.11.16 and the frozen lockfile |
| Prepare output already exists | Use a new directory; `run`/`verify` use the existing protocol |
| New protocol requires a reason | Provide a specific reason and preserve the ledger history; do not reselect based on the test |
| This protocol is already being evaluated | Check the running process and wait for it to finish |
| Scenario/summary integrity failed | Keep the failed copy for audit and restore outputs with the expected hash |
| FinPlot/display unavailable | Install the `charts` extra; use a desktop or `QT_QPA_PLATFORM=offscreen` for PNG output |
| Insufficient warm-up/no interval | Check the boundary and history length; do not fill prices to bypass the error |

The evaluator uses `fcntl` for locking; the validated runtime is Linux. Windows support has not been implemented.

Local backups should keep the exact snapshot, source, frozen inventory, detailed results, and ledger together. Reports/CSVs help read the results; they do not replace the checkpoints and snapshot needed for recomputation.

**Next:** the [project README](../README.md) links to the quickstart and documentation index.
