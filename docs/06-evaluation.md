# 06 — Frozen Evaluation

## Contents

- [Why lock the protocol](#why-lock-the-protocol)
- [Fixed decisions](#fixed-decisions)
- [Prepare, run, verify, and report](#prepare-run-verify-and-report)
- [Resume and integrity](#resume-and-integrity)
- [Diagnostics and summaries](#diagnostics-and-summaries)
- [Artifacts and charts](#artifacts-and-charts)

## Why lock the protocol

Validation was used to select lambda. If the test is used to choose a seed, lambda, or fee level that gives a better result, the test becomes selection data too.

The protocol records the choices and model inventory **before the first test evaluation**. The experiment succeeds by evaluating the predeclared configuration correctly, even if RL loses to a baseline. All policies use the [same simulator and metrics](04-simulator.md).

## Fixed decisions

| Item | Decision |
|---|---|
| Primary | Lambda 2, seed 42 checkpoint from the learning run |
| Reference | Lambda 0, seed 42 checkpoint |
| Training / validation | Preserve the segment through 2020 / 2021–2022 |
| Declared test | 2023-01-01 to 2026-10-02 |
| Actual test | 2023-01-03 to 2026-10-02, 940 intervals |
| Snapshot | Exact SHA256 used during training |
| Seeds | 42, 7, 21, 84, 123 |
| Cost scenarios | 0/10/20 bps; primary always uses 10 bps |
| Each run | Reset flat/$100,000; greedy with epsilon 0 |
| Model updates | Q/visits are read-only; no training during evaluation |

The two seed-42 models are copied byte-for-byte, not retrained on validation. The eight additional models are four seeds × two lambdas; each is trained for 100 episodes on the original training segment, with the same bins/settings. Lambda is not reselected per seed using validation.

Scenario matrix:

| Group | Run count |
|---|---:|
| RL: 5 seeds × 2 lambdas × 3 costs | 30 |
| Deterministic baselines: 5 policies × 3 costs | 15 |
| Random: 5 seeds × 3 costs | 15 |
| Total | 60 |

Each deterministic baseline runs once per cost; it is not replicated as five independent samples. Baseline reward uses lambda 2; its financial accounting uses the same engine. Reward is not used to compare P&L between two lambdas.

The primary table has eight rows: two RL policies and six baselines at seed 42/10 bps. Other seeds describe variability; they do not replace the primary result.

## Prepare, run, verify, and report

The commands below use the archived snapshot and existing source learning run. The prepare output directory must be new:

```bash
uv run indexpilot-evaluate prepare --data data/raw/aapl_daily_2015-01-01_to_2026-10-06_processed.parquet --source-run outputs/stage-3/aapl-default --config configs/stage-4.toml --output-dir outputs/stage-4/aapl-frozen
uv run indexpilot-evaluate run --protocol-dir outputs/stage-4/aapl-frozen
uv run indexpilot-evaluate verify --protocol-dir outputs/stage-4/aapl-frozen
uv run indexpilot-evaluate report --protocol-dir outputs/stage-4/aapl-frozen
```

| Command | Work performed |
|---|---|
| `prepare` | Validate source manifest/selection/state metadata/data hash; prepare 10 models; save protocol ID and hashes |
| `run` | Recheck frozen inputs/runtime, slice causal test, evaluate 60 scenarios, and export results |
| `verify` | Recompute in a separate verification directory; compare data/decisions/artifacts |
| `report` | Read saved artifacts and generate `report.md`; does not evaluate or train |

`prepare` locks the expected data hash from the validated source and checks it before/after loading and before publication. It also checks the source manifest, selection, primary checkpoints, and training logs to detect changes during training/copying. If an input changes, preparation aborts and cleans up its temporary output; it does not publish a protocol.

`prepare` checks boundaries and warm-up to lock intended coverage; it does not roll out on the test. Warm-up takes `max(20, risk_window)+1` rows before the first eligible session. Warm-up is excluded from the equity curve, and positions are not carried from validation into the test. The run ends at the final open; the simulator handles the liquidation fee in the final interval.

Cost sensitivity **keeps the same Q table**, but does not require identical actions. For example, higher fees can change equity/drawdown and move the account into another state bin; the same Q table may then select a different action.

## Resume and integrity

The protocol locks dataset/source/checkpoint/training-log hashes, effective configuration, bins/actions, Python/core package versions, `uv.lock`, Git revision, and fingerprints of the package's Python modules.

Changing docs does not change the calculation fingerprint. Subsequent hardening/refactoring of Python changed the fingerprint: the old AAPL protocol remains unchanged and must be replayed with revision `b6c550d` in a separate checkout. On main, run/verify requires a protocol prepared with the main code; do not edit old hashes to bypass checks. Changes to Python logic or the lockfile are detected. The numerical runtime must match Python/core package versions; platform and optional GUI versions are recorded as provenance.

If a run is interrupted, rerun the same command. Completed scenarios are hash-checked before reuse; only missing scenarios are calculated.

The completed manifest is written to a temporary file in the same directory, flushed/fsynced, then atomically replaced. A crash before publication does not leave a truncated manifest JSON; resuming reuses completed scenarios and regenerates summaries. If the manifest was published but the completion ledger event was not written, the next run checks the manifest and adds a recovered event.

Once a run is complete, the `run` command checks summaries, scenario artifacts, and protocol, then returns the saved results. Edited files are not silently overwritten. The tool does not download a new snapshot or swap a checkpoint to bypass an error.

The experiment ledger at `outputs/stage-4/experiment-ledger.jsonl` is an append-only hash chain with process locking. Events include prepared, started, scenario_completed, completed, failed, and verified. Verification failures receive their own record.

After a test has been completed and recorded in the ledger, preparing a new protocol requires a reason and a new directory, for example:

```text
--output-dir outputs/stage-4/aapl-new-protocol
--reason "Rebuild the inventory in a separate environment"
```

The reason records the purpose of the new experiment; do not use another run to select parameters based on the test. Verification does not create a new selection round or modify the locked inventory.

## Diagnostics and summaries

| Diagnostic | Meaning |
|---|---|
| Action frequencies | Rates of targets −1/−0.5/0/+0.5/+1; `HoldPosition` is separate |
| Flat decisions | Target 0, not exposure before the order |
| Active intervals | Holdings after the decision are nonzero |
| Gross exposure | abs(units_after × execution_price / equity_before) |
| Long/short intervals | Sign of holdings after the decision |
| Unseen states | State had no visits during training |
| Trade duration | Calendar days from opening to closing |
| Reward breakdown | Totals for gross-return fractions, cost fractions, lambda × risk, and reward |
| Drawdown | MDD peak/trough/recovery and longest underwater calendar duration |

Fixed labels are `no_trades`, `sparse_trades` for 1–4 closed trades, `mostly_flat` when flat decisions ≥95%, `unseen_states_present`, and `insolvent`. Labels help interpretation; they do not change the policy or selection.

For example, target 0 can be chosen when pre-decision exposure is +0.5: this is **a flat action that closes the position**, not an account that was already flat.

Seed summaries report mean/median/sample standard deviation/min/max of finite values, along with counts for finite/undefined/infinite/not applicable/insolvent. With fewer than two finite values, standard deviation is N/A. Infinity is not replaced with a large number, and failed runs are not omitted.

Paired comparison calculates lambda 2 − lambda 0 **for the same seed and cost**. It does not combine the equity curves from five seeds into a portfolio. Seed variability measures randomness in learning from the same history, not a confidence interval for future market results.

Yearly summaries record `expected_start_date`/`expected_end_date` by year, taken from eligible intervals in the test segment before policy execution. `partial_year` indicates an incomplete year horizon or actual coverage that misses expected boundaries; insolvency in December is still detected. This does not verify completeness against an exchange calendar.

Yearly summaries use **one continuous episode**. Returns are compounded by interval `end_date`; fees are assigned to the same intervals; closed trades are counted separately. Trade P&L is not used as calendar return because a trade can span multiple years. Insolvency retains actual coverage and debt; no synthetic returns are added through the end of the horizon.

## Artifacts and charts

```text
protocol.json
frozen_models/
preparation/
run_manifest.json
primary_summary.csv/json
scenario_summary.csv/json
seed_summary.csv/json
paired_comparison.csv/json
yearly_summary.csv/json
diagnostics.json
runs/<scenario_id>/
    accounting/<policy>/
        equity.parquet
        ledger.parquet
        orders.parquet
        trades.parquet
        intervals.parquet
    decisions.parquet
    transitions.parquet       # RL only
    score.json
    diagnostics.json
    scenario.json
    completion.json
figures/
report.md
verification-*/
```

Score/manifest files retain intended and actual coverage/status; reward is recorded separately from financial P&L. Completion hashes allow checking/resuming each scenario.

FinPlot reads the artifacts and displays equity/drawdown in two panels:

```bash
uv run indexpilot-chart --run-dir outputs/stage-4/aapl-frozen
uv run indexpilot-chart --run-dir outputs/stage-4/aapl-frozen --cost-bps 20
uv run indexpilot-chart --run-dir outputs/stage-4/aapl-frozen --seeds --risk-lambda 2 --cost-bps 10
```

Report/chart commands do not train or reevaluate policies. Detailed outputs are not in Git; interpret results alongside the archived inputs needed for replay.

**Next:** the [project README](../README.md) links to results and reproduction instructions.
