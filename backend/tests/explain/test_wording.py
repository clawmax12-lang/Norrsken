import pytest

from preflight.contracts import SimulatorName
from preflight.explain import format_timestamp
from preflight.explain.wording import format_range, scene_label, simulator_label
from tests.factories import make_concept


@pytest.mark.parametrize(
    ("seconds", "expected"),
    [
        (0, "0:00"),
        (3, "0:03"),
        (59, "0:59"),
        (65, "1:05"),
        (15.0, "0:15"),
        (2.5, "0:02.5"),
        (2.96, "0:03"),
        (59.97, "1:00"),
    ],
)
def test_format_timestamp(seconds: float, expected: str) -> None:
    assert format_timestamp(seconds) == expected


@pytest.mark.parametrize("seconds", [-0.1, float("nan"), float("inf")])
def test_format_timestamp_rejects_values_that_are_not_a_time(seconds: float) -> None:
    with pytest.raises(ValueError, match="timestamp"):
        format_timestamp(seconds)


def test_format_range() -> None:
    assert format_range(3, 6) == "0:03-0:06"


def test_scene_label_is_one_based_and_quotes_the_scene_text() -> None:
    scene = make_concept().scenes[1]

    assert scene_label(1, scene) == "scene 2, 0:03-0:06, 'Notes that organise themselves'"


def test_simulator_labels_use_prd_wording() -> None:
    assert simulator_label(SimulatorName.TRIBE_V2) == "brain sim"
    assert simulator_label(SimulatorName.GEMINI_PANEL) == "simulated viewer panel"
