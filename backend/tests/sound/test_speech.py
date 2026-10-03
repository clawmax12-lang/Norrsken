import pytest

from preflight.errors import ProviderError
from preflight.llm import SpeechAudio
from preflight.sound.speech import DELIVERY, GeminiSpeech


class FakeSpeechBackend:
    """Test-only stand-in for Gemini text-to-speech."""

    def __init__(self) -> None:
        self.requests: list[tuple[str, str, str]] = []
        self.error: Exception | None = None

    async def synthesize_speech(self, *, model: str, text: str, voice: str) -> SpeechAudio:
        self.requests.append((model, text, voice))
        if self.error:
            raise self.error
        return SpeechAudio(b"\x01\x00" * 2400, 24_000, input_tokens=9, output_tokens=60)


def speech(tmp_path, backend: FakeSpeechBackend, voice: str = "Kore") -> GeminiSpeech:
    return GeminiSpeech(backend, model="tts-model", voice=voice, cache_dir=tmp_path / "cache")


async def test_the_line_is_sent_with_a_delivery_direction_and_the_chosen_voice(tmp_path) -> None:
    backend = FakeSpeechBackend()

    clip = await speech(tmp_path, backend).synthesize("Notes that organise themselves")

    assert backend.requests == [
        ("tts-model", f"{DELIVERY}: Notes that organise themselves", "Kore")
    ]
    assert (clip.sample_rate, clip.input_tokens, clip.output_tokens) == (24_000, 9, 60)


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


async def test_a_failed_call_is_not_cached(tmp_path) -> None:
    backend = FakeSpeechBackend()
    backend.error = ProviderError("quota")

    with pytest.raises(ProviderError):
        await speech(tmp_path, backend).synthesize("Acme Notes")

    backend.error = None
    await speech(tmp_path, backend).synthesize("Acme Notes")
    assert len(backend.requests) == 2
