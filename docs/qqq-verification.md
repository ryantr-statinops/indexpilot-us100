# QQQ verification evidence

The QQQ / Nasdaq-100 ETF experiment completed under the [predeclared rules](qqq-experiment.md). This record reports checks actually performed on 2026-10-09; data, checkpoints, and detailed outputs remain local and are not included in a Git clone.

## Identity

| Property | Value |
|---|---|
| Calculation revision | `e2c4cba4f1d51876dad8373d1ffbf41e72050cd0` |
| Numerical runtime | Python 3.11.16 and frozen `uv.lock` |
| Dataset SHA256 | `4db7a3175dfe288b7a440a2b3cd4996e0322420429fd55feeb3dce8c7d02b9f2` |
| Protocol ID | `16af504702802ec895620d84c64550f5919fbc1933af9151cced8f5c4b8db2dd` |
| Primary / reference lambda | 0.5 / 0 |
| Primary seed / cost | 42 / 10 bps |
| Actual frozen test coverage | 2023-01-03 to 2026-10-02; 940 open-to-open intervals |
| Model inventory / scenarios | 10 / 60 |

The snapshot contains 2,956 rows from 2015-01-02 to 2026-10-05; its final row is outside the frozen test horizon. Dates are unique and adjusted prices are finite, positive, and non-null. Exchange-calendar completeness is not verified. All 60 scenarios completed without insolvency on this snapshot.

## Checks performed

- The implementation checkout and a fresh cloned checkout/virtual environment each passed **206 tests**.
- Independent evaluation replay matched **60/60 scenarios**, including summary files, decisions, RL transitions, accounting Parquet, scores, and diagnostics.
- Restored the exact archive into a fresh checkout at the calculation revision, installed frozen dependencies with Python 3.11.16, supplied the relocated snapshot with `--data`, and independently replayed **60/60** again.
- Reconciled 60 terminal events; maximum account error was 2.910e-11 USD, maximum net trade P&L error 3.783e-10 USD, and maximum order/interval fee difference 2.183e-11 USD.
- Checked Q/visits for all 30 RL scenarios: arrays stayed unchanged and read-only. The two seed-42 model files were byte-identical to their QQQ source checkpoints.
- Cash stayed exactly $100,000 at all costs; buy and hold had exactly two orders at all costs. Final holdings were zero, with terminal fees included in the last interval.
- Rendered and visually inspected offscreen primary and five-seed equity/drawdown PNGs. Report identity and replay paths were checked; report and primary PNG also generated in the clean checkout.
- The existing AAPL archive SHA256 remained `4a47e5d16e617a14328b37be2869cc2e7825b803f14bcfba4ff8c63e68789889`. The shared ledger retained its append-only history.

## Local evidence and archive

- `outputs/stage-4/qqq-frozen/audit.json`
- `outputs/stage-4/qqq-frozen/local_verification.json` and `verification-*/verification.json`
- `outputs/stage-4/qqq_clean_environment_verification.json`
- `outputs/stage-4/qqq_reproduction_archive_manifest.json`
- `outputs/stage-4/experiment-ledger.jsonl`

Archive: `outputs/stage-4/qqq-reproduction.tar.gz`, 18,851,540 bytes. SHA256: `1d7d90c25d797ae6b248cd91254aee0c515593a61bc713532c3d549b178f527e`.

The archive contains the QQQ raw/processed snapshot and manifest, Stage 2 baselines, Stage 3 learning run, frozen protocol/models/results, audit, local verification record, report/figures, and a ledger snapshot. Full replay directories are excluded to avoid duplicating scenario tables; fresh verification recreates them. The clean-environment verification record is stored separately and identifies the tested archive hash.

Reports can differ in their replay paths after relocation; verification compares the financial/accounting artifacts rather than expecting identical report path text. See [reproduction](08-reproduction.md) and [results](07-results.md) for usage and interpretation. Passing these checks establishes reproducibility and accounting consistency, not predictive skill or live profitability.
