import pytest

from preflight.ports import SpeechClip
from preflight.sound.voice_timing import (
    BEAT_S,
    MIN_SCENE_S,
    fit_to_voice,
    snap_to_beats,
    spoken_seconds,
    time_to_voice,
)
from tests.factories import make_concept
from tests.sound.helpers import tone_clip


class SecondsPerWordSpeech:
    """A narrator whose clip lasts ``seconds_per_word`` per word (plus silent padding)."""

    def __init__(self, seconds_per_word: float = 0.4) -> None:
        self.seconds_per_word = seconds_per_word
        self.calls: list[str] = []

    async def synthesize(self, text: str) -> SpeechClip:
        self.calls.append(text)
        return tone_clip(len(text.split()) * self.seconds_per_word)


def _on_beats(values: list[float]) -> bool:
    return all(v / BEAT_S == pytest.approx(round(v / BEAT_S)) for v in values)


def test_snapping_keeps_the_total_and_lands_every_cut_on_a_beat() -> None:
    lengths = snap_to_beats([2.3, 3.1, 3.4, 3.2], 12)

    assert sum(lengths) == pytest.approx(12)
    assert _on_beats(lengths)


def test_a_long_line_gets_a_longer_scene_and_short_lines_share_the_rest() -> None:
    lengths = fit_to_voice([3, 3, 3, 3], [1.0, 4.0, 1.0, 1.0], 12)

    assert sum(lengths) == pytest.approx(12)
    assert lengths[1] == max(lengths)
    assert lengths[1] >= 4.0 / 1.1
    assert min(lengths) >= MIN_SCENE_S - BEAT_S


def test_lines_that_cannot_all_fit_are_scaled_to_the_body_length() -> None:
    lengths = fit_to_voice([3, 3, 3, 3], [5.0, 5.0, 5.0, 5.0], 12)

    assert sum(lengths) == pytest.approx(12)
    assert _on_beats(lengths)


async def test_spoken_seconds_measures_voice_without_its_silence() -> None:
    seconds = await spoken_seconds(SecondsPerWordSpeech(0.5), ["one two", "", "a b c d"])

    assert seconds[0] == pytest.approx(1.0, abs=0.15)
    assert seconds[1] == 0.0
    assert seconds[2] == pytest.approx(2.0, abs=0.15)


async def test_time_to_voice_retimes_the_body_and_keeps_the_end_card() -> None:
    concept = make_concept()
    voices = ("Short", "A much longer line that needs real time to say", "Short", "Short", None)
    voiced = concept.model_copy(
        update={
            "scenes": tuple(
                s.model_copy(update={"voice": v})
                for s, v in zip(concept.scenes, voices, strict=True)
            )
        }
    )
    speech = SecondsPerWordSpeech(0.4)

    timed = await time_to_voice(voiced, speech)

    lengths = [s.t_end - s.t_start for s in timed.scenes]
    assert lengths[1] == max(lengths[:-1])
    assert (timed.scenes[-1].t_start, timed.scenes[-1].t_end) == (12.0, 15.0)
    assert [s.t_start for s in timed.scenes[1:]] == [s.t_end for s in timed.scenes[:-1]]
    assert len(speech.calls) == 4


async def test_a_concept_without_voice_lines_is_left_alone() -> None:
    concept = make_concept()
    speech = SecondsPerWordSpeech()

    assert await time_to_voice(concept, speech) is concept
    assert speech.calls == []
