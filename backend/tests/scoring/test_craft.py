import pytest

from preflight.contracts import Beat, BeatKind, SoundRecord
from preflight.scoring.craft import craft_for
from tests.factories import SHA
from tests.sound.helpers import make_spec


def sound(coverage: float, lufs: float) -> SoundRecord:
    return SoundRecord(
        variant_id="A",
        tested_video_sha256=SHA,
        final_video_sha256=SHA,
        final_video_path="video-final.mp4",
        narrated=True,
        bpm=120,
        integrated_lufs=lufs,
        true_peak_dbtp=-1.5,
        voice_coverage=coverage,
    )


def test_pace_counts_the_beats_before_the_end_card_and_the_longest_still_stretch() -> None:
    craft = craft_for(make_spec(), None, "en")

    assert craft.events_per_s == pytest.approx(4 / 12, abs=0.01)  # hook and three cuts
    assert craft.longest_still_s == pytest.approx((90 - 8) / 30, abs=0.01)
    assert craft.voice_coverage is None and craft.integrated_lufs is None
    assert len(craft.issues) == 1
    assert "nothing happens on screen for 2.7 s around 0:00.3" in craft.issues[0]


def test_a_busy_cut_with_a_full_voice_at_feed_loudness_has_no_issues() -> None:
    spec = make_spec()
    busy = tuple(
        Beat(kind=BeatKind.WORD, frame=frame, frames=6, scene=frame // 90)
        for frame in range(20, 360, 45)
    )
    dense = spec.model_copy(update={"beats": (*spec.beats, *busy)})

    craft = craft_for(dense, sound(0.8, -14.0), "en")

    assert craft.longest_still_s < 2.0
    assert craft.issues == ()
    assert craft.voice_coverage == 0.8


def test_a_thin_voice_and_a_quiet_mix_are_flagged_in_the_brief_language() -> None:
    craft = craft_for(make_spec(), sound(0.3, -20.0), "sv")

    assert any("rösten täcker bara 30 %" in issue for issue in craft.issues)
    assert any("-20.0 LUFS" in issue for issue in craft.issues)


def test_an_older_spec_without_beats_is_measured_but_not_judged() -> None:
    craft = craft_for(make_spec().model_copy(update={"beats": ()}), sound(0.2, -30.0), "en")

    assert craft.issues == ()
    assert craft.events_per_s == 0
