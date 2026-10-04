import pytest
from pydantic import ValidationError

from preflight.contracts import Brief, TokenSavings
from tests.factories import make_brief, make_concept, make_result


def test_brief_round_trips_through_json() -> None:
    brief = make_brief(brand_color="#12ab34", goal_note="get beta users")
    assert Brief.model_validate_json(brief.model_dump_json()) == brief


def test_brief_defaults_to_showcase_render_mode() -> None:
    assert make_brief().render_mode.value == "showcase"


@pytest.mark.parametrize(
    "overrides",
    [
        {"one_liner": "x" * 141},
        {"screenshots": ("uploads/1.png", "uploads/2.png")},
        {"screenshots": ("a.png", "a.png", "b.png")},
        {"brand_color": "red"},
        {"unexpected": 1},
    ],
)
def test_brief_rejects_invalid_input(overrides: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        make_brief(**overrides)


def test_concept_scene_lookup_clamps_to_the_video() -> None:
    concept = make_concept()
    assert concept.scene_at(0).t_start == 0
    assert concept.scene_at(15).t_end == 15
    assert concept.scene_at(7.5).t_start == 6


def test_concept_rejects_long_hook_and_gaps() -> None:
    with pytest.raises(ValidationError, match="hook"):
        make_concept(hook="one two three four five six seven eight nine")
    concept = make_concept()
    gapped = concept.scenes[:1] + concept.scenes[2:]
    with pytest.raises(ValidationError):
        make_concept(scenes=gapped)


def test_result_requires_aligned_unit_range_series() -> None:
    with pytest.raises(ValidationError, match="within"):
        make_result(values=(0.5, 1.5))
    with pytest.raises(ValidationError, match="primary_series"):
        make_result(primary_series="missing")
    with pytest.raises(ValidationError, match="length"):
        make_result(series={"signal": (0.5,) * 15, "other": (0.1,)})


def test_token_savings_are_derived_not_stored() -> None:
    savings = TokenSavings(calls=2, input_tokens_original=1000, input_tokens_sent=600)
    assert savings.tokens_saved == 400
    assert savings.percent == 40.0
    assert savings.model_dump()["percent"] == 40.0
    assert TokenSavings().percent == 0.0
    with pytest.raises(ValidationError):
        TokenSavings(input_tokens_original=1, input_tokens_sent=2)
