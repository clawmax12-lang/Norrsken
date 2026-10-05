import pytest

from preflight.errors import ProviderError, TransientProviderError
from preflight.llm import SpeechAudio
from preflight.sound.speech import DELIVERY, GeminiSpeech, rate_wait_s


class FakeSpeechBackend:
    """Test-only stand-in for Gemini text-to-speech."""

    def __init__(self) -> None:
        self.requests: list[tuple[str, str, str, str | None]] = []
        self.errors: list[Exception] = []
        self.error: Exception | None = None

    async def synthesize_speech(
        self, *, model: str, text: str, voice: str, style: str | None = None
    ) -> SpeechAudio:
        self.requests.append((model, text, voice, style))
        if self.errors:
            raise self.errors.pop(0)
        if self.error:
            raise self.error
        return SpeechAudio(b"\x01\x00" * 2400, 24_000, input_tokens=9, output_tokens=60)


def speech(tmp_path, backend: FakeSpeechBackend, voice: str = "Kore") -> GeminiSpeech:
    return GeminiSpeech(backend, model="tts-model", voice=voice, cache_dir=tmp_path / "cache")


def test_delivery_asks_for_a_calm_persuasive_mature_voice() -> None:
    folded = DELIVERY.casefold()
    assert "calm" in folded and "persuasive" in folded and "woman" in folded
    assert "young" not in folded and "energetic" not in folded
    assert "unhurried" not in folded
    assert not folded.startswith("say ")


async def test_the_line_is_sent_with_a_delivery_direction_and_the_chosen_voice(tmp_path) -> None:
    backend = FakeSpeechBackend()

    clip = await speech(tmp_path, backend).synthesize("Notes that organise themselves")

    assert backend.requests == [("tts-model", "Notes that organise themselves", "Kore", DELIVERY)]
    assert (clip.sample_rate, clip.input_tokens, clip.output_tokens) == (24_000, 9, 60)


async def test_a_gemini_2_5_voice_gets_its_delivery_in_the_prompt_instead(tmp_path) -> None:
    backend = FakeSpeechBackend()
    narrator = GeminiSpeech(
        backend, model="gemini-2.5-pro-preview-tts", voice="Leda", cache_dir=tmp_path
    )

    await narrator.synthesize("Betala i ett steg")

    [(_, text, _, style)] = backend.requests
    assert text == f"Say it like a {DELIVERY}: Betala i ett steg"
    assert style is None


async def test_a_repeated_line_is_served_from_the_cache_without_a_second_call(tmp_path) -> None:
    backend = FakeSpeechBackend()
    voice = speech(tmp_path, backend)

    first = await voice.synthesize("Acme Notes")
    second = await voice.synthesize("Acme Notes")

    assert len(backend.requests) == 1
    assert second.pcm == first.pcm
    assert (second.input_tokens, second.output_tokens) == (0, 0)  # nothing was spent


async def test_a_different_voice_or_text_is_not_served_from_the_cache(tmp_path) -> None:
    backend = FakeSpeechBackend()

    await speech(tmp_path, backend, "Kore").synthesize("Acme Notes")
    await speech(tmp_path, backend, "Aoede").synthesize("Acme Notes")
    await speech(tmp_path, backend, "Kore").synthesize("Acme Notes today")

    assert len(backend.requests) == 3


async def test_a_transient_quota_error_is_retried_then_cached(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("preflight.sound.speech._RETRY_WAIT_S", (0.0, 0.0, 0.0))
    backend = FakeSpeechBackend()
    backend.errors = [TransientProviderError("429"), TransientProviderError("429")]
    voice = speech(tmp_path, backend)

    first = await voice.synthesize("Acme Notes")
    second = await voice.synthesize("Acme Notes")

    assert len(backend.requests) == 3
    assert second.pcm == first.pcm
    assert (second.input_tokens, second.output_tokens) == (0, 0)


async def test_exhausted_quota_errors_are_not_cached(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("preflight.sound.speech._RETRY_WAIT_S", (0.01, 0.0))
    backend = FakeSpeechBackend()
    backend.errors = [TransientProviderError("429"), TransientProviderError("quota")]

    with pytest.raises(TransientProviderError, match="quota"):
        await speech(tmp_path, backend).synthesize("Acme Notes")

    backend.errors = []
    await speech(tmp_path, backend).synthesize("Acme Notes")
    assert len(backend.requests) == 3


async def test_a_failed_call_is_not_cached(tmp_path) -> None:
    backend = FakeSpeechBackend()
    backend.error = ProviderError("quota")

    with pytest.raises(ProviderError):
        await speech(tmp_path, backend).synthesize("Acme Notes")

    backend.error = None
    await speech(tmp_path, backend).synthesize("Acme Notes")
    assert len(backend.requests) == 2


async def test_a_spent_tts_model_hands_over_to_the_fallback_for_the_rest_of_the_film(
    tmp_path,
) -> None:
    backend = FakeSpeechBackend()
    backend.errors = [TransientProviderError("429 quota")]
    narrator = GeminiSpeech(
        backend,
        model="tts-model",
        voice="Kore",
        cache_dir=tmp_path,
        fallback_models=("tts-lite",),
    )

    await narrator.synthesize("Betala i ett steg")
    await narrator.synthesize("Klar på sekunder")

    assert [model for model, *_ in backend.requests] == ["tts-model", "tts-lite", "tts-lite"]
    assert narrator.model == "tts-lite"


def test_only_a_per_minute_quota_is_worth_waiting_for() -> None:
    assert rate_wait_s(TransientProviderError("429 ... Please retry in 16.39s.")) == 16.39
    assert rate_wait_s(TransientProviderError("429 ... Please retry in 7h9m18.4s.")) is None
    assert rate_wait_s(TransientProviderError("429")) is None


async def test_a_per_minute_quota_waits_on_the_same_model_instead_of_falling_back(
    tmp_path, monkeypatch
) -> None:
    waits: list[float] = []

    async def no_sleep(seconds: float) -> None:
        waits.append(seconds)

    monkeypatch.setattr("preflight.sound.speech.asyncio.sleep", no_sleep)
    backend = FakeSpeechBackend()
    backend.errors = [TransientProviderError("429 limit: 3. Please retry in 20.5s.")]
    narrator = GeminiSpeech(
        backend, model="tts-model", voice="Kore", cache_dir=tmp_path, fallback_models=("tts-lite",)
    )

    await narrator.synthesize("Betala i ett steg")

    assert [model for model, *_ in backend.requests] == ["tts-model", "tts-model"]
    assert waits == [21.5]
