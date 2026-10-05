from preflight.contracts import BriefField
from preflight.planning.claims import ClaimRef, CopyLine, copy_problems
from tests.factories import make_brief

BRIEF = make_brief(
    one_liner="Notes that organise themselves for 2 400 teams",
    audience="busy founders on iOS",
)


def problems(*texts: str, claims: tuple[ClaimRef, ...] = ()) -> list[str]:
    lines = [CopyLine(f"line {i}", text) for i, text in enumerate(texts, start=1)]
    return copy_problems(lines, claims, BRIEF)


def test_free_phrasing_of_brief_facts_passes() -> None:
    assert problems("Your notes sort themselves", "Made for busy founders") == []


def test_numbers_must_come_from_the_brief_even_with_other_separators() -> None:
    assert problems("Trusted by 2400 teams") == []
    result = problems("Trusted by 5000 teams")
    assert len(result) == 1 and "5000" in result[0]


def test_names_the_brief_never_mentions_are_rejected() -> None:
    assert problems("Works great on iOS") == []
    result = problems("Works with Shopify and Notion")
    assert len(result) == 1
    assert "Shopify" in result[0] and "Notion" in result[0]


def test_a_name_inside_a_brief_compound_is_known() -> None:
    brief = make_brief(one_liner="En blixtsnabb Stripe-checkout med Apple Pay")

    assert (
        copy_problems(
            [CopyLine("voice", "Med Stripe och Apple Pay betalar kunden direkt.")], (), brief
        )
        == []
    )
    assert copy_problems([CopyLine("voice", "Med Klarna betalar kunden direkt.")], (), brief) != []
    hanging = CopyLine("voice", "Vår Stripe- och Apple Pay-kassa tar bort hinder.")
    assert copy_problems([hanging], (), brief) == []
    assert copy_problems([CopyLine("voice", "Vår Shopify-kassa är klar.")], (), brief) != []


def test_the_first_word_of_a_sentence_is_not_a_name() -> None:
    assert problems("Organise everything. Then relax") == []


def test_title_case_lines_are_not_read_as_names() -> None:
    assert problems("Notes That Organise Themselves") == []


def test_superlatives_and_quotes_are_rejected() -> None:
    assert any("superlative" in p for p in problems("The fastest notes app"))
    assert any("superlative" in p for p in problems("Sveriges bästa app"))
    assert any("quotation" in p for p in problems('"I love it" says a founder'))


def test_a_claim_must_quote_its_field_verbatim() -> None:
    good = ClaimRef("Teams use it", BriefField.ONE_LINER, "for 2 400  TEAMS")
    bad = ClaimRef("Used by founders", BriefField.ONE_LINER, "used by founders")

    assert problems(claims=(good,)) == []
    result = problems(claims=(bad,))
    assert len(result) == 1 and "one_liner" in result[0]
