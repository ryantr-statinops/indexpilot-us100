# IndexPilot US100 Documentation

QQQ is an ETF proxy for Nasdaq-100; the project operates on one price series and does not construct a top-100 stock universe. This documentation describes the **single-asset Nasdaq-100 research prototype using QQQ**, from the price snapshot through the simulator, Q-learning, frozen test, and reproduction workflow. It is organized around how to use and understand the project; you do not need to read its implementation history to understand how it works.

## Contents

- [Where to start](#where-to-start)
- [Chapters](#chapters)
- [Two reading paths](#two-reading-paths)
- [Documentation and artifacts](#documentation-and-artifacts)

## Where to start

- To understand the project: [01 — Overview](01-overview.md).
- To run it or view results: [02 — Quickstart](02-quickstart.md).
- To see what the RL agent learned: [07 — Results](07-results.md).
- To replay the exact experiment: [08 — Reproduction](08-reproduction.md).

For example, if you only want to view equity and drawdown, restore the saved artifacts and use `indexpilot-chart`. To check whether the results can actually be reproduced, also restore the exact snapshot and models, then use `indexpilot-evaluate verify`. These tasks have different prerequisites.

## Chapters

| Chapter | Main topics |
|---|---|
| [01 — Overview](01-overview.md) | QQQ/Nasdaq-100 scope, stack, and architecture |
| [02 — Quickstart](02-quickstart.md) | Setup, commands, archived experiment, and new snapshots |
| [03 — Data](03-data.md) | Adjusted prices, quality checks, causal features, hashes, and splits |
| [04 — Simulator](04-simulator.md) | Account, post-fee targets, reward, baselines, trades, and metrics |
| [05 — Q-learning](05-q-learning.md) | State bins, actions, Bellman update, training, and selection |
| [06 — Evaluation](06-evaluation.md) | Locked protocol, 60 scenarios, diagnostics, resume, and verification |
| [07 — Results](07-results.md) | Validation/test results, activity, seeds, costs, and limitations |
| [08 — Reproduction](08-reproduction.md) | Archive restore, runtime/hashes, report/chart, and troubleshooting |

Additional experiment records:

- [QQQ experiment rules](qqq-experiment.md): decisions recorded before QQQ training/test.
- [QQQ verification evidence](qqq-verification.md): checked hashes, replay, accounting, tests, and archive.

The previous AAPL experiment remains a [historical result](07-results.md#historical-aapl-experiment) with its own [reproduction instructions](08-reproduction.md#historical-aapl-reproduction). Its models and data are separate.

## Two reading paths

### Understand the project

[01](01-overview.md) → [03](03-data.md) → [04](04-simulator.md) → [05](05-q-learning.md) → [06](06-evaluation.md) → [07](07-results.md).

Follow the data timeline, how cash and positions change, how the agent learns, how the test is kept separate, and what the results mean.

### Run the project

[02](02-quickstart.md) → [08](08-reproduction.md), then [07](07-results.md) to compare and interpret the results.

For a fresh download, read [03](03-data.md) and treat it as a new snapshot. For exact reproduction, use the archive with the recorded hash. A Git clone does not contain market data or checkpoints.

## Documentation and artifacts

- The docs explain the mechanisms and select tables that help interpret results.
- Config files are version-controlled parameters.
- Data, manifests, checkpoints, and detailed outputs are stored locally, outside Git.
- Generated reports, CSV/JSON, Parquet, and PNG files are created from artifacts; they do not replace the inputs needed for verification.

Capital, fees, reward, and metrics are defined in the [simulator chapter](04-simulator.md); the saved frozen `protocol.json` is the source of truth for the protocol. For further research, create a separate experiment with a clear reason instead of changing choices after seeing the published test.

**Next:** [01 — Overview](01-overview.md) or [02 — Quickstart](02-quickstart.md). The root [project README](../README.md) is the introduction.
