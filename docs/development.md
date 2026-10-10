# Development workflow

Use small, sequential changes on `dev`. Each commit contains one file and one independent task. Check the staged diff, run the relevant checks, commit, and push before starting the next change. Add a new shared module before switching its callers; preserve existing imports when moving an interface.

## Code conventions

Ruff targets Python 3.11 with a line length of 100. The lint rules cover import layout (`I`), import errors (`E4`), statement layout (`E7`), syntax errors (`E9`), and Python correctness checks (`F`). Use the formatter for quotes, spacing, and multiline expressions.

Keep functions focused on one responsibility and use names that describe domain operations. The portfolio accounting engine remains shared by baselines and RL through `Policy`. Keep artifact integrity checks in the shared completion module, scenario orchestration in the workflow, and report rendering separate from file output. The data adapter, transformations, quality statistics, and snapshot persistence have separate helpers. Add abstractions when a concrete extension needs them.

Run Ruff through `uvx` without adding it to application dependencies or changing `uv.lock`:

```bash
uvx ruff==0.17.0 check src tests
uvx ruff==0.17.0 format --check --output-format concise src tests
```

To apply conventions, work on one file at a time:

```bash
uvx ruff==0.17.0 format path/to/file.py
uvx ruff==0.17.0 check --fix path/to/file.py
uvx ruff==0.17.0 format path/to/file.py
```

Review lint fixes as well as formatting. Keep calls with side effects when removing unused assignments; use only safe automatic fixes.

## Regression checks

Run the tests that exercise each change before its commit. At the end of a refactor round, run its related test group:

```bash
uv run --frozen pytest -q tests/test_simulator.py tests/test_environment.py tests/test_transition.py tests/test_reconciliation.py
uv run --frozen pytest -q tests/test_final_workflow.py tests/test_final_artifacts.py tests/test_final_history.py tests/test_final_reproducibility.py tests/test_final_runner.py
uv run --frozen pytest -q tests/test_final_report.py tests/test_final_chart.py tests/test_chart.py
uv run --frozen pytest -q tests/test_data_processing.py tests/test_cli.py tests/test_learning_cli.py
```

Finish a complete refactor with the full suite and both Ruff checks:

```bash
uv run --frozen pytest -q
uvx ruff==0.17.0 check src tests
uvx ruff==0.17.0 format --check --output-format concise src tests
```

Tests use synthetic data and temporary directories. The optional offscreen PNG test runs when FinPlot is installed. Add regression cases for an actual behavior gap; avoid tests that only repeat helper implementation details.

## Compatibility and frozen experiments

Preserve CLI entry points, callable interfaces, serialized schemas, accounting event order, fee allocation, and deterministic numerical outputs. Compare report content using identical persisted values; provenance fields such as revision, protocol ID, and creation time naturally differ for newly prepared experiments.

Published protocols fingerprint Python source and the dependency lock. Refactoring and formatting change those fingerprints even when numerical behavior stays the same. Replay historical experiments using the recorded calculation revision described in [the reproduction guide](08-reproduction.md); prepare a new protocol when evaluating the current code. Keep historical data, checkpoints, protocols, and results intact.

Push completed changes to `dev` in commit order. Prepare the `dev` to `main` PR description with the changes, regression evidence, and any limitations after final checks pass.
