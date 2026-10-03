"""The studio against the real ffmpeg, with a stand-in voice (test-only; never used in the app)."""

import pytest

from preflight.errors import ProviderError, SoundError
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
    return SoundStudio(Ffmpeg(), voice, voice="Kore", tts_model="tts-test")


async def test_a_narrated_cut_records_what_was_said_and_how_loud_it_is(tmp_path) -> None:
    voice = FakeVoice()
    asked = request(tmp_path)

    record = await studio(voice).finish(asked)

    assert voice.said == ["Notes that organise themselves", "Acme Notes"]
    assert record.narrated and record.voice == "Kore" and record.tts_model == "tts-test"
    assert [line.text for line in record.narration] == voice.said
    assert record.tested_video_sha256 == asked.video_sha256
    assert record.final_video_sha256 == sha256_file(asked.output_path)
    assert record.final_video_sha256 != record.tested_video_sha256
    assert record.integrated_lufs == pytest.approx(-14.0, abs=0.7)
    assert record.true_peak_dbtp <= -1.0
    assert (record.tts_input_tokens, record.tts_output_tokens) == (14, 80)
    assert record.note is None
    assert sha256_file(asked.video_path) == asked.video_sha256  # the tested render is untouched


async def test_narration_off_gives_music_and_effects_and_says_so(tmp_path) -> None:
    record = await studio(None).finish(request(tmp_path))

    assert not record.narrated and record.voice is None and record.narration == ()
    assert record.note == "Narration is off."
    assert record.cues


async def test_a_voice_outage_degrades_to_music_and_effects_instead_of_failing(tmp_path) -> None:
    voice = FakeVoice()
    voice.error = ProviderError("quota exhausted")
    asked = request(tmp_path)

    record = await studio(voice).finish(asked)

    assert not record.narrated
    assert record.note == "Narration unavailable: quota exhausted"
    assert asked.output_path.is_file()


async def test_a_line_too_long_for_its_scene_is_sped_up_to_fit(tmp_path) -> None:
    voice = FakeVoice(seconds=1.3)  # slightly longer than the CTA's window of about 1.25 s
    asked = request(tmp_path)

    record = await studio(voice).finish(asked)

    assert [line.text for line in record.narration] == [
        "Notes that organise themselves",
        "Acme Notes",
    ]


async def test_a_line_that_cannot_fit_even_when_sped_up_is_left_out(tmp_path) -> None:
    voice = FakeVoice(seconds=6.0)

    record = await studio(voice).finish(request(tmp_path))

    assert not record.narrated
    assert record.note == "No line fit its scene; music and effects only."


async def test_a_missing_ffmpeg_raises_a_sound_error(tmp_path) -> None:
    broken = SoundStudio(Ffmpeg("/no/such/ffmpeg", "/no/such/ffprobe"), None)

    with pytest.raises(SoundError):
        await broken.finish(request(tmp_path))
