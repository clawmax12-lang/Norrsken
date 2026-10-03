from hypothesis import given
from hypothesis import strategies as st

from preflight.planning.grounding import (
    FUNCTION_WORDS,
    find_violations,
    ungrounded_words,
    words,
)
from tests.factories import make_brief, make_concept

SOURCE = "Notes that organise themselves"


def test_words_ignore_case_and_punctuation() -> None:
    assert words("Hello, WORLD! It's 3-4 pm.") == ("hello", "world", "it", "s", "3", "4", "pm")


def test_text_built_from_source_words_is_grounded() -> None:
    assert ungrounded_words("THEMSELVES: organise notes!", SOURCE) == ()


def test_function_words_are_allowed_but_content_words_are_not() -> None:
    assert ungrounded_words("The notes for your team save hours", SOURCE) == (
        "team",
        "save",
        "hours",
    )


def test_numbers_must_come_from_the_source() -> None:
    assert ungrounded_words("10x notes", SOURCE) == ("10x",)
    assert ungrounded_words("Top 3 notes", "Top 3 notes apps") == ()


def test_inflections_count_as_new_words() -> None:
    assert ungrounded_words("organises", SOURCE) == ("organises",)


def test_each_offending_word_is_reported_once_in_order() -> None:
    assert ungrounded_words("fast fast notes faster", SOURCE) == ("fast", "faster")


def test_empty_source_grounds_only_function_words() -> None:
    assert ungrounded_words("the best", "") == ("best",)


@given(st.lists(st.sampled_from((*words(SOURCE), "The", "NOTES", "of")), min_size=1, max_size=8))
def test_any_recombination_of_source_words_is_grounded(chosen: list[str]) -> None:
    assert ungrounded_words(", ".join(chosen).upper(), SOURCE) == ()


@given(st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=12))
def test_a_word_absent_from_source_and_function_words_is_flagged(word: str) -> None:
    if word in words(SOURCE) or word in FUNCTION_WORDS:
        return
    assert ungrounded_words(f"notes {word}", SOURCE) == (word,)


@given(st.text(max_size=60), st.text(max_size=60))
def test_grounding_is_deterministic_and_idempotent_on_source_text(text: str, source: str) -> None:
    assert ungrounded_words(text, source) == ungrounded_words(text, source)
    assert ungrounded_words(source, source) == ()


def test_grounded_concept_has_no_violations() -> None:
    assert find_violations(make_concept(), make_brief()) == ()


def test_violations_name_the_location_field_and_words() -> None:
    concept = make_concept(hook="Save hours every week", cta="Join 10000 founders")

    violations = find_violations(concept, make_brief())

    assert [v.location for v in violations] == ["hook", "cta"]
    assert violations[0].words == ("save", "hours", "every", "week")
    assert violations[0].describe() == (
        'hook: text "Save hours every week" uses "save", "hours", "every", "week", which are not '
        "in brief field one_liner; use only words from that field"
    )


def test_violation_text_is_singular_for_one_word() -> None:
    concept = make_concept(cta="Acme Notes today")

    (violation,) = find_violations(concept, make_brief())

    assert violation.describe().endswith(
        'uses "today", which is not in brief field product_name; use only words from that field'
    )


def test_scene_violations_are_numbered_from_one() -> None:
    concept = make_concept()
    scenes = list(concept.scenes)
    scenes[2] = scenes[2].model_copy(update={"text": "Loved by thousands"})

    violations = find_violations(concept.model_copy(update={"scenes": tuple(scenes)}), make_brief())

    assert [v.location for v in violations] == ["scene 3"]


def test_the_product_name_may_appear_in_any_field() -> None:
    concept = make_concept(cta="Acme Notes for founders", cta_source_field="audience")

    assert find_violations(concept, make_brief(audience="Startup founders")) == ()


def test_optional_field_that_is_unset_grounds_nothing() -> None:
    concept = make_concept(cta="Launch day", cta_source_field="goal_note")

    (violation,) = find_violations(concept, make_brief(goal_note=None))

    assert violation.words == ("launch", "day")
