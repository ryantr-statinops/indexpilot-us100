import pytest

from indexpilot_us100.agents import LearningConfig, load_learning_config


def test_schedule():
    config = LearningConfig()
    assert config.epsilon(0) == 1
    assert config.epsilon(1000) == 0.05


@pytest.mark.parametrize(
    "kwargs",
    [
        dict(episodes=0),
        dict(alpha=0),
        dict(gamma=2),
        dict(epsilon_decay=0),
        dict(epsilon_min=1, epsilon_start=0.5),
        dict(lambdas=(0.5,)),
        dict(lambdas=(0, 0)),
        dict(lambdas=(0, float("nan"))),
        dict(train_end="2022-01-01"),
        dict(test_start="bad"),
    ],
)
def test_invalid(kwargs):
    with pytest.raises(ValueError):
        LearningConfig(**kwargs)


def test_toml(tmp_path):
    path = tmp_path / "config.toml"
    path.write_text("[learning]\nepisodes=2\nlambdas=[0,0.5]\n")
    simulation, learning = load_learning_config(path)
    assert simulation.seed == 42 and learning.lambdas == (0, 0.5)
    path.write_text("[learning]\ntypo=1\n")
    with pytest.raises(ValueError):
        load_learning_config(path)
