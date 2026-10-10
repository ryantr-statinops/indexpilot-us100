# Package API and imports

Use each package's `__init__.py` as the import path for public interfaces. This keeps
application code independent of the module that implements a class or function.

```python
from indexpilot_us100.agents import QLearningAgent, train_agent
from indexpilot_us100.environment import TradingEnvironment
from indexpilot_us100.metrics import compute_metrics
from indexpilot_us100.portfolio import SimulationConfig, run_episode
from indexpilot_us100.evaluation.final import (
    EvaluationConfig,
    prepare_protocol,
    run_evaluation,
)
```

The root package intentionally exposes only `__version__`; import domain APIs from
their subpackage. For example, use `indexpilot_us100.portfolio`, not
`indexpilot_us100` or `indexpilot_us100.portfolio.simulator` in application code.

## Public packages

| Package | Use it for | Examples of public names |
|---|---|---|
| `indexpilot_us100.data` | Downloading and processing market data | `download_daily`, `normalize_download`, `process_raw_csv`, `summarize` |
| `indexpilot_us100.portfolio` | Portfolio accounting, policies, market inputs, and simulation | `Account`, `SimulationConfig`, `MarketData`, `run_episode`, `rebalance`, `baseline_policies` |
| `indexpilot_us100.environment` | Turning simulation records into agent observations and transitions | `TradingEnvironment`, `Trajectory`, `Transition` |
| `indexpilot_us100.agents` | Q-learning configuration, state encoding, training, and experiments | `QLearningAgent`, `LearningConfig`, `train_agent`, `run_experiments`, `encode_state` |
| `indexpilot_us100.metrics` | Portfolio performance metrics and reports | `compute_metrics`, `MetricsReport`, `sharpe_ratio`, `drawdown_curve` |
| `indexpilot_us100.evaluation` | Exporting results, JSON/hash helpers, and charts | `export_results`, `export_learning`, `create_chart`, `write_json_atomic` |
| `indexpilot_us100.evaluation.final` | Preparing, running, verifying, and reporting a frozen evaluation | `EvaluationConfig`, `prepare_protocol`, `run_evaluation`, `verify_evaluation`, `generate_report` |

The package's `__all__` is the authoritative list of public names. This page lists
common entry points; use `help(package)` or inspect `package.__all__` for the complete
list. For example:

```python
import indexpilot_us100.portfolio as portfolio

print(portfolio.__all__)
help(portfolio.run_episode)
```

## Choosing an import path

Use a package facade when depending on a public API:

```python
from indexpilot_us100.portfolio import SimulationConfig, run_episode
```

Within a package, modules can import implementation details directly using relative
imports. For example, `portfolio` implementation modules may use
`from .account import Account`. Avoid importing another package's private module from
application code; promote a stable cross-package interface through the owning package's
`__all__` instead.

Direct module imports are appropriate for private helpers, command-line `main`
functions, and tests that deliberately patch implementation details:

```python
from indexpilot_us100.evaluation import cli

cli.main()
```

The old module paths remain available for compatibility. New application code should
prefer the package facade so implementation files can move without requiring callers to
change imports.

## Lazy imports and optional dependencies

Public names are resolved the first time they are accessed, then cached on the package.
This keeps a plain package import lightweight and avoids importing unrelated
implementations during package initialization. It does not change how a function runs
once called.

Chart functions are exported by `indexpilot_us100.evaluation`, but creating a chart
requires the optional chart dependencies. Install the `charts` extra for that feature:

```bash
uv sync --extra charts
```

Importing another evaluation API does not itself create a chart or access the network.

## Command-line tools

Use the installed command-line entry points for user-facing commands instead of calling
private CLI modules from application code. For example:

```bash
uv run indexpilot-evaluate --help
uv run indexpilot-chart --help
```

See the [quickstart](02-quickstart.md) for project commands and the
[development workflow](development.md) for contribution conventions.
