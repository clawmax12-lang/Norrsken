from hypothesis import given
from hypothesis import strategies as st

from preflight.llm import CallUsage, TokenLedger


def test_empty_ledger_reports_zero_savings() -> None:
    snapshot = TokenLedger().snapshot()

    assert (snapshot.calls, snapshot.tokens_saved, snapshot.percent) == (0, 0, 0.0)


def test_generations_alone_never_report_savings() -> None:
    ledger = TokenLedger()
    ledger.record_generation(CallUsage(1000, 50))

    snapshot = ledger.snapshot()

    assert snapshot.input_tokens_original == snapshot.input_tokens_sent == 1000
    assert snapshot.tokens_saved == 0


def test_savings_are_the_measured_difference() -> None:
    ledger = TokenLedger()
    ledger.record_generation(CallUsage(600, 40))
    ledger.record_compression(tokens_before=500, tokens_after=100)

    snapshot = ledger.snapshot()

    assert (snapshot.input_tokens_original, snapshot.input_tokens_sent) == (1000, 600)
    assert snapshot.percent == 40.0
    assert snapshot.output_tokens == 40


def test_growth_is_not_counted_as_negative_savings() -> None:
    ledger = TokenLedger()
    ledger.record_compression(tokens_before=10, tokens_after=30)

    assert ledger.snapshot().tokens_saved == 0
    assert ledger.snapshot().calls == 1


@given(
    st.lists(st.tuples(st.integers(0, 10_000), st.integers(0, 10_000)), max_size=20),
    st.lists(st.integers(0, 5_000), max_size=20),
)
def test_sent_never_exceeds_original(
    compressions: list[tuple[int, int]], inputs: list[int]
) -> None:
    ledger = TokenLedger()
    for before, after in compressions:
        ledger.record_compression(tokens_before=before, tokens_after=after)
    for tokens in inputs:
        ledger.record_generation(CallUsage(tokens, 1))

    snapshot = ledger.snapshot()

    assert snapshot.input_tokens_sent <= snapshot.input_tokens_original
