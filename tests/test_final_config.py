import pytest
from indexpilot_us100.evaluation.final.config import EvaluationConfig


def test_default_matrix():
    assert EvaluationConfig().scenario_count==60
    assert EvaluationConfig.from_toml('configs/stage-4.toml')==EvaluationConfig()


@pytest.mark.parametrize('kwargs',[dict(seeds=(42,42)),dict(seeds=(7,)),dict(seeds=(42,True)),dict(costs_bps=(0,20)),dict(costs_bps=(10,float('nan'))),dict(primary_lambda=0),dict(test_end='2022-01-01'),dict(test_start='bad')])
def test_invalid(kwargs):
    with pytest.raises(ValueError): EvaluationConfig(**kwargs)


@pytest.mark.parametrize("label", ["", "  ", 42, "QQQ\nAAPL", "QQQ\rAAPL"])
def test_invalid_instrument_label(label):
    with pytest.raises(ValueError, match="instrument_label"):
        EvaluationConfig(instrument_label=label)


def test_instrument_label_is_optional_and_read_from_toml(tmp_path):
    config_path = tmp_path / "evaluation.toml"
    config_path.write_text('instrument_label = "QQQ / Nasdaq-100 ETF"\n')
    assert EvaluationConfig.from_toml(config_path).instrument_label == "QQQ / Nasdaq-100 ETF"
    assert EvaluationConfig.from_toml("configs/stage-4.toml").instrument_label is None
