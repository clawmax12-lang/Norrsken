import pytest
from pydantic import BaseModel

from preflight.errors import PreflightValidationError, ProviderError, TransientProviderError
from preflight.llm import GeminiClient, TextPart, TokenLedger
from preflight.llm.backend import BackendResponse
from tests.llm.fakes import FakeCompressor, FakeGeminiBackend


class Answer(BaseModel):
    word: str
    n: int


GOOD = '{"word": "hi", "n": 1}'
BAD = '{"word": "hi", "n": "many"}'
BIG_CONTEXT = "context " * 400


def make_client(backend, **kwargs) -> GeminiClient:
    return GeminiClient(backend, "gemini-test", retry_delay_s=0, **kwargs)


async def test_returns_validated_model_and_records_usage() -> None:
    backend = FakeGeminiBackend(GOOD)
    ledger = TokenLedger()

    answer = await make_client(backend, ledger=ledger).generate_json(
        Answer, "system", [TextPart("go")]
    )

    assert answer == Answer(word="hi", n=1)
    snapshot = ledger.snapshot()
    assert (snapshot.input_tokens_sent, snapshot.output_tokens, snapshot.tokens_saved) == (
        100,
        20,
        0,
    )


async def test_proxied_answers_record_measured_condense_savings() -> None:
    proxied = BackendResponse(
        GOOD, input_tokens=80, output_tokens=20, uncompressed_input_tokens=100
    )
    ledger = TokenLedger()

    await make_client(FakeGeminiBackend(proxied), ledger=ledger).generate_json(
        Answer, "system", [TextPart("go")]
    )

    snapshot = ledger.snapshot()
    assert (snapshot.calls, snapshot.input_tokens_sent, snapshot.input_tokens_original) == (
        1,
        80,
        100,
    )
    assert snapshot.tokens_saved == 20


async def test_invalid_answer_gets_exactly_one_repair_with_the_error_fed_back() -> None:
    backend = FakeGeminiBackend(BAD, GOOD)

    measured = await make_client(backend).generate_json_measured(Answer, "system", [TextPart("go")])

    assert measured.value.n == 1
    assert (measured.usage.input_tokens, measured.usage.output_tokens) == (200, 40)
    repair_texts = backend.texts(1)
    assert BAD in repair_texts
    assert any("n: Input should be a valid integer" in text for text in repair_texts)
    assert backend.texts(0) == ["go"]


async def test_repair_error_message_does_not_echo_model_input_values() -> None:
    backend = FakeGeminiBackend('{"word": "SECRET-INPUT", "n": "x"}', GOOD)

    await make_client(backend).generate_json(Answer, "system", [TextPart("go")])

    problems = backend.texts(1)[-1]
    assert "SECRET-INPUT" not in problems
    assert "errors.pydantic.dev" not in problems


async def test_second_invalid_answer_raises_validation_error() -> None:
    backend = FakeGeminiBackend(BAD, "not json")

    with pytest.raises(PreflightValidationError, match="after one repair"):
        await make_client(backend).generate_json(Answer, "system", [TextPart("go")])

    assert len(backend.calls) == 2


async def test_semantic_validator_problems_trigger_the_same_repair() -> None:
    backend = FakeGeminiBackend(GOOD, '{"word": "bye", "n": 1}')

    def reject_hi(answer: Answer) -> list[str]:
        return ["word must not be 'hi'"] if answer.word == "hi" else []

    answer = await make_client(backend).generate_json(
        Answer, "system", [TextPart("go")], validate=reject_hi
    )

    assert answer.word == "bye"
    assert "word must not be 'hi'" in backend.texts(1)[-1]


async def test_transient_error_is_retried_once() -> None:
    backend = FakeGeminiBackend(TransientProviderError("429"), GOOD)

    answer = await make_client(backend).generate_json(Answer, "system", [TextPart("go")])

    assert answer.n == 1
    assert len(backend.calls) == 2


async def test_second_transient_error_propagates() -> None:
    backend = FakeGeminiBackend(TransientProviderError("a"), TransientProviderError("b"))

    with pytest.raises(TransientProviderError, match="b"):
        await make_client(backend).generate_json(Answer, "system", [TextPart("go")])


async def test_permanent_provider_error_is_not_retried() -> None:
    backend = FakeGeminiBackend(ProviderError("400"), GOOD)

    with pytest.raises(ProviderError, match="400"):
        await make_client(backend).generate_json(Answer, "system", [TextPart("go")])

    assert len(backend.calls) == 1


async def test_compressible_text_is_compressed_and_savings_are_measured() -> None:
    backend = FakeGeminiBackend(GOOD)
    ledger = TokenLedger()
    compressor = FakeCompressor("context " * 100)
    client = make_client(backend, ledger=ledger, compressor=compressor)

    await client.generate_json(
        Answer, "system", [TextPart("instructions"), TextPart(BIG_CONTEXT, compressible=True)]
    )

    assert compressor.seen == [BIG_CONTEXT]
    assert backend.texts() == ["instructions", "context " * 100]
    snapshot = ledger.snapshot()
    assert snapshot.calls == 1
    assert snapshot.tokens_saved == 300
    assert snapshot.input_tokens_original == snapshot.input_tokens_sent + 300


async def test_non_compressible_text_never_reaches_the_compressor() -> None:
    backend = FakeGeminiBackend(GOOD)
    compressor = FakeCompressor("tiny")

    await make_client(backend, compressor=compressor).generate_json(
        Answer, "system", [TextPart(BIG_CONTEXT)]
    )

    assert compressor.seen == []
    assert backend.texts() == [BIG_CONTEXT]


async def test_compression_that_does_not_shrink_keeps_the_original() -> None:
    backend = FakeGeminiBackend(GOOD)
    ledger = TokenLedger()
    compressor = FakeCompressor(BIG_CONTEXT + " longer")

    await make_client(backend, ledger=ledger, compressor=compressor).generate_json(
        Answer, "system", [TextPart(BIG_CONTEXT, compressible=True)]
    )

    assert backend.texts() == [BIG_CONTEXT]
    assert ledger.snapshot().tokens_saved == 0


async def test_compressor_returning_none_counts_nothing() -> None:
    backend = FakeGeminiBackend(GOOD)
    ledger = TokenLedger()

    await make_client(backend, ledger=ledger, compressor=FakeCompressor(None)).generate_json(
        Answer, "system", [TextPart(BIG_CONTEXT, compressible=True)]
    )

    assert backend.counted == []
    assert ledger.snapshot().calls == 0


async def test_unmeasurable_compression_falls_back_to_the_original() -> None:
    backend = FakeGeminiBackend(GOOD)
    backend.count_error = ProviderError("count failed")
    ledger = TokenLedger()

    await make_client(backend, ledger=ledger, compressor=FakeCompressor("short")).generate_json(
        Answer, "system", [TextPart(BIG_CONTEXT, compressible=True)]
    )

    assert backend.texts() == [BIG_CONTEXT]
    assert ledger.snapshot().calls == 0


async def test_model_property_reports_the_configured_model() -> None:
    assert make_client(FakeGeminiBackend()).model == "gemini-test"


async def test_a_spent_model_falls_back_to_the_next_and_cools_down() -> None:
    now = [0.0]
    backend = FakeGeminiBackend(TransientProviderError("429 quota"), GOOD, GOOD, GOOD)
    client = make_client(backend, fallback_models=("flash-b", "flash-c"), clock=lambda: now[0])

    for _ in range(2):
        assert await client.generate_json(Answer, "system", [TextPart("go")]) == Answer(
            word="hi", n=1
        )
        assert client.answered_by == "flash-b"
    now[0] = 61.0
    await client.generate_json(Answer, "system", [TextPart("go")])

    assert backend.models == ["gemini-test", "flash-b", "flash-b", "gemini-test"]
    assert client.answered_by == "gemini-test"


async def test_when_every_model_fails_the_first_is_retried_once_then_it_raises() -> None:
    backend = FakeGeminiBackend(*(TransientProviderError(str(n)) for n in range(3)))
    client = make_client(backend, fallback_models=("flash-b",))

    with pytest.raises(TransientProviderError, match="2"):
        await client.generate_json(Answer, "system", [TextPart("go")])

    assert backend.models == ["gemini-test", "flash-b", "gemini-test"]
