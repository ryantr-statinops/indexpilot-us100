from dataclasses import asdict

from indexpilot_us100.evaluation.final.config import EvaluationConfig
from indexpilot_us100.evaluation.final.matrix import scenarios


def test_declared_sixty_runs():
    rows = scenarios({"evaluation_config": asdict(EvaluationConfig())})
    assert len(rows) == 60 and len({row["scenario_id"] for row in rows}) == 60
    assert sum(row["kind"] == "rl" for row in rows) == 30
    assert sum(row["kind"] == "random" for row in rows) == 15
    assert sum(row["kind"] == "deterministic" for row in rows) == 15
    assert {row["cost_bps"] for row in rows} == {0, 10, 20}
