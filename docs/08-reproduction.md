# 08 — Reproducing the Experiment

## Contents

- [Requirements](#requirements)
- [Restore the archive in a clean checkout](#restore-the-archive-in-a-clean-checkout)
- [Replay and verify](#replay-and-verify)
- [Generate a report and PNG charts from artifacts](#generate-a-report-and-png-charts-from-artifacts)
- [Prepare a new protocol from source](#prepare-a-new-protocol-from-source)
- [Historical AAPL reproduction](#historical-aapl-reproduction)
- [Troubleshooting](#troubleshooting)

## Requirements

Exact reproduction uses the same snapshot, frozen models, protocol, and compatible calculation code. Git contains code/configuration/docs; market data, models, detailed outputs, and archives are local.

The QQQ archive is `outputs/stage-4/qqq-reproduction.tar.gz` (18,851,540 bytes). Its manifest is `outputs/stage-4/qqq_reproduction_archive_manifest.json`. Obtain the archive separately from the experiment machine, subject to data-use permissions.

```text
Archive SHA256:
1d7d90c25d797ae6b248cd91254aee0c515593a61bc713532c3d549b178f527e
Dataset SHA256:
4db7a3175dfe288b7a440a2b3cd4996e0322420429fd55feeb3dce8c7d02b9f2
Protocol ID:
16af504702802ec895620d84c64550f5919fbc1933af9151cced8f5c4b8db2dd
Calculation revision:
e2c4cba4f1d51876dad8373d1ffbf41e72050cd0
```

The archive includes the QQQ source snapshot/manifest, Stage 2 baselines, Stage 3 learning run, frozen models/preparation/protocol, saved runs/summaries/manifest, report/figures, audit and local verification record, and a ledger snapshot. Full duplicate verification directories are excluded. See [verification evidence](qqq-verification.md) for the clean-environment record stored separately.

## Restore the archive in a clean checkout

Use a separate checkout so another experiment is not overwritten:

```bash
git clone https://github.com/ryantr-statinops/indexpilot-us100.git indexpilot-qqq-frozen
cd indexpilot-qqq-frozen
git checkout --detach e2c4cba4f1d51876dad8373d1ffbf41e72050cd0
uv sync --python 3.11.16 --frozen --extra dev --extra charts

sha256sum /absolute/path/qqq-reproduction.tar.gz
tar -xzf /absolute/path/qqq-reproduction.tar.gz \
  data/qqq \
  outputs/stage-2/qqq-default \
  outputs/stage-3/qqq-default \
  outputs/stage-4/qqq-frozen \
  outputs/stage-4/experiment-ledger.jsonl
```

Compare the archive SHA256 before extraction. Replace the archive path with its actual location. Keep protocol/model/data hashes unchanged. Documentation-only commits after the calculation revision remain compatible; changes anywhere in the Python package or lockfile can change the fingerprint. Read current instructions on main and replay in the frozen checkout if needed.

## Replay and verify

The protocol can record an absolute snapshot path from the original machine. Supply the relocated exact file with `--data`:

```bash
uv run indexpilot-evaluate run \
  --protocol-dir outputs/stage-4/qqq-frozen \
  --data data/qqq/qqq_daily_2015-01-01_to_2026-10-06_processed.parquet

uv run indexpilot-evaluate verify \
  --protocol-dir outputs/stage-4/qqq-frozen \
  --data data/qqq/qqq_daily_2015-01-01_to_2026-10-06_processed.parquet
```

For a completed archive, `run` checks integrity and reuses persisted results. `verify` recomputes all 60 scenarios in a new `verification-*` directory and compares summary files, decisions, RL transitions, accounting Parquet, metrics, and diagnostics. Timestamp/Git fields in exporter manifests are excluded from the numerical comparison; provenance artifacts remain hash-protected. The verified event is appended to the local ledger.

An interrupted run can resume; completed scenarios are checked before reuse. Do not run `prepare` in the restored frozen directory. Fresh Yahoo downloads can revise adjustments and do not replace the exact snapshot.

Synthetic tests are independent of market snapshots and Yahoo:

```bash
uv run pytest -q
```

The QQQ calculation revision passed 206 tests in both the implementation checkout and a fresh environment. Local and relocated clean-environment verification each replayed 60/60. Reports contain location-specific replay commands, so moving the archive changes report paths; the financial artifacts still match exactly.

## Generate a report and PNG charts from artifacts

These commands read saved results without training or evaluation:

```bash
uv run indexpilot-evaluate report --protocol-dir outputs/stage-4/qqq-frozen

uv run indexpilot-chart --run-dir outputs/stage-4/qqq-frozen \
  --save-png outputs/stage-4/qqq-frozen/figures/primary.png

QT_QPA_PLATFORM=offscreen uv run indexpilot-chart \
  --run-dir outputs/stage-4/qqq-frozen --seeds --risk-lambda 0.5 --cost-bps 10 \
  --save-png outputs/stage-4/qqq-frozen/figures/primary-seeds.png
```

The report defaults to `report.md` in the run directory; `--output` selects another destination. It uses the frozen instrument label and actual protocol/data paths. The English [results chapter](07-results.md) is a separate editorial interpretation; the generated report also retains existing Vietnamese explanatory sections.

FinPlot has equity/drawdown panels. `--cost-bps` chooses a declared cost; `--seeds` and `--risk-lambda` select all seeds for that lambda. `--save-png` renders with Qt and closes the window. Offscreen rendering is available without a desktop display; core evaluation does not require the `charts` extra.

```python
import polars as pl

root = "outputs/stage-4/qqq-frozen"
print(pl.read_csv(f"{root}/primary_summary.csv"))
print(pl.read_csv(f"{root}/paired_comparison.csv"))
```

## Prepare a new protocol from source

To prepare a new experiment on current compatible code, restore the exact QQQ source snapshot/learning run and ledger, choose a fresh directory, and record a reason:

```bash
uv run indexpilot-evaluate prepare \
  --data data/qqq/qqq_daily_2015-01-01_to_2026-10-06_processed.parquet \
  --source-run outputs/stage-3/qqq-default \
  --config configs/stage-4-qqq.toml \
  --output-dir outputs/stage-4/qqq-reprepared \
  --reason "Rebuild QQQ inventory from archived training inputs"
```

For the published QQQ source, primary lambda is 0.5 and reference is 0. Preparation copies two seed-42 checkpoints and trains eight additional models on training only. It does not evaluate the test, and the new preparation timestamp creates a new protocol ID. Run a newly prepared protocol using its own directory; restore the published archive to replay the original protocol.

A fresh training run may select another lambda. Apply the [predeclared reference rule](qqq-experiment.md) and create its own config/protocol before test evaluation; do not edit the published QQQ config to match a new test outcome. Reprocessing raw CSV is useful for learning the pipeline, but exact reproduction still requires matching Parquet bytes/hash.

## Historical AAPL reproduction

The earlier AAPL archive and protocol remain separate and were preserved during the QQQ migration:

```text
Archive: outputs/stage-4/aapl-reproduction.tar.gz
Archive SHA256: 4a47e5d16e617a14328b37be2869cc2e7825b803f14bcfba4ff8c63e68789889
Dataset SHA256: 042605225d9f9dc91ac983ceb13079f09077a569bd485dd06774263f994db3cc
Protocol ID: 5fbce9eb3c97815487c57b7eaca4502390562e37ed062609d72c87ba189ec18b
Calculation revision: b6c550da754fec519d14b7a0a9610a219b303904
```

In a separate checkout of the original AAPL calculation revision with Python 3.11.16 and its frozen lockfile, restore:

```bash
tar -xzf /absolute/path/aapl-reproduction.tar.gz \
  data/raw/aapl_daily_2015-01-01_to_2026-10-06_processed.parquet \
  outputs/stage-3/aapl-default \
  outputs/stage-4/aapl-frozen \
  outputs/stage-4/experiment-ledger.jsonl

uv run indexpilot-evaluate verify \
  --protocol-dir outputs/stage-4/aapl-frozen \
  --data data/raw/aapl_daily_2015-01-01_to_2026-10-06_processed.parquet
```

The original AAPL revision had 175 tests and recorded 60-scenario verification. Those are historical checks, not new AAPL recomputation during the QQQ migration. Current report/chart tools can read saved AAPL artifacts; absent an instrument label, generated report identity is neutral single-asset. Exact AAPL run/verify needs its compatible original code, not QQQ checkpoints or an edited fingerprint.

## Troubleshooting

| Problem | Resolution |
|---|---|
| Missing snapshot/models/results after clone | Obtain and restore the correct separate archive |
| Data hash changed | Use the exact snapshot; `--data` changes location, not required bytes |
| Model/log/source hash changed | Restore original archived artifacts and compare their manifest |
| Code or lockfile changed | Use the experiment's frozen revision or prepare a separate protocol |
| Numerical runtime differs | Use Python 3.11.16 and the frozen lockfile in a separate environment |
| Prepare output exists | Choose a new directory; use `run`/`verify` for an existing protocol |
| New protocol requires reason | Record a specific purpose and preserve ledger history |
| Source selection does not match primary | Use that source run's validation selection and predeclared reference rule before evaluating test |
| Protocol already being evaluated | Check the active process and wait for completion |
| Scenario/summary integrity failed | Preserve the failed copy for audit and restore correct outputs |
| FinPlot/display unavailable | Install `charts`; use desktop or `QT_QPA_PLATFORM=offscreen` for PNG |
| Insufficient warm-up/coverage | Inspect boundaries and source history; do not fill prices or shorten the frozen horizon |

Locking uses `fcntl`; Linux is the verified runtime. Windows support has not been implemented. Keep the exact snapshot, source run, frozen inventory/results, and ledger together in backups. Report/CSV files do not replace inputs needed for recomputation.

**Next:** the [project README](../README.md) links to quickstart and documentation.
