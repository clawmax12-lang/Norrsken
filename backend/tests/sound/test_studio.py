"""The studio against the real ffmpeg, with a stand-in voice (test-only; never used in the app)."""

import pytest

from preflight.errors import NarrationError, ProviderError, SoundError
from preflight.hashing import sha256_file
from preflight.ports import SoundRequest, SpeechClip
from preflight.sound import Ffmpeg, SoundStudio
from tests.sound.helpers import make_spec, needs_ffmpeg, silent_video, tone_clip

pytestmark = needs_ffmpeg


class FakeVoice:
    """Speaks every line as a tone of a chosen length; can be told to fail."""

    def __init__(self, seconds: float = 1.2) -> None:
        self.seconds = seconds
        self.said: list[str] = []
        self.error: Exception | None = None

    async def synthesize(self, text: str) -> SpeechClip:
        self.said.append(text)
        if self.error:
            raise self.error
        return tone_clip(self.seconds)


def request(tmp_path) -> SoundRequest:
    video = silent_video(tmp_path / "v.mp4")
    return SoundRequest(
        spec=make_spec(),
        video_path=video,
        video_sha256=sha256_file(video),
        output_path=tmp_path / "final.mp4",
        work_dir=tmp_path / "work",
    )


def studio(voice: FakeVoice | None) -> SoundStudio:
    return SoundStudio(Ffmpeg(), voice, voice="Leda", tts_model="tts-test")


async def test_a_narrated_cut_records_what_was_said_and_how_loud_it_is(tmp_path) -> None:
    voice = FakeVoice()
    asked = request(tmp_path)

    record = await studio(voice).finish(asked)

    assert record.narrated and record.voice == "Leda" and record.tts_model == "tts-test"
    assert record.narration
    assert voice.said == [line.text for line in record.narration]
    assert record.tested_video_sha256 == asked.video_sha256
    assert record.final_video_sha256 == sha256_file(asked.output_path)
    assert record.final_video_sha256 != record.tested_video_sha256
    assert record.integrated_lufs == pytest.approx(-14.0, abs=0.7)
    assert record.true_peak_dbtp <= -1.0
    assert record.tts_input_tokens >= 0 and record.tts_output_tokens >= 0
    assert record.note is None
    assert sha256_file(asked.video_path) == asked.video_sha256


async def test_narration_off_gives_ambience_and_effects_and_says_so(tmp_path) -> None:
    record = await studio(None).finish(request(tmp_path))

    assert not record.narrated and record.voice is None and record.narration == ()
    assert record.note == "Narration is off."
    assert record.cues


async def test_a_voice_outage_stops_the_finish_instead_of_shipping_a_silent_ad(tmp_path) -> None:
    voice = FakeVoice()
    voice.error = ProviderError("quota exhausted")
    asked = request(tmp_path)

    with pytest.raises(NarrationError, match="quota exhausted"):
        await studio(voice).finish(asked)

    assert not asked.output_path.exists()


async def test_a_line_too_long_for_its_scene_is_sped_up_to_fit(tmp_path) -> None:
    voice = FakeVoice(seconds=1.3)
    record = await studio(voice).finish(request(tmp_path))

    assert record.narrated


async def test_a_line_too_long_for_its_window_is_trimmed_not_dropped(tmp_path) -> None:
    voice = FakeVoice(seconds=6.0)

    record = await studio(voice).finish(request(tmp_path))

    assert record.narrated and record.narration


async def test_a_missing_ffmpeg_raises_a_sound_error(tmp_path) -> None:
    broken = SoundStudio(Ffmpeg("/no/such/ffmpeg", "/no/such/ffprobe"), None)

    with pytest.raises(SoundError):
        await broken.finish(request(tmp_path))
