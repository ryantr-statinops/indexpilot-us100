import pytest

from indexpilot_us100.portfolio.config import SimulationConfig


def test_defaults():
    assert SimulationConfig().cost_rate == 0.001


@pytest.mark.parametrize(
    "kwargs",
    [
        dict(initial_equity=0),
        dict(cost_bps=-1),
        dict(cost_bps=10000),
        dict(risk_window=1),
        dict(risk_window=2.5),
        dict(risk_lambda=-1),
        dict(seed=-1),
        dict(seed=True),
        dict(annualization=0),
        dict(risk_free_annual=-1),
        dict(cost_bps=float("nan")),
    ],
)
def test_invalid(kwargs):
    with pytest.raises(ValueError):
        SimulationConfig(**kwargs)


def test_toml(tmp_path):
    path = tmp_path / "config.toml"
    path.write_text("seed = 5\ncost_bps = 0\n")
    assert SimulationConfig.from_toml(path).seed == 5
    path.write_text("typo = 1\n")
    with pytest.raises(ValueError, match="Unknown"):
        SimulationConfig.from_toml(path)
