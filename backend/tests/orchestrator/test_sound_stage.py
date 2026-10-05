"""Sound covers every rendered video and resumes; only a lost voice pauses the run."""

from preflight.contracts import RunRecord, RunState, SoundRecord, Step, StepStatus
from preflight.errors import NarrationError, SoundError
from tests.orchestrator.fakes import Failures, FakeSoundFinisher, World


def sound_events(world: World):
    return [e for e in world.store.read_events(world.project_id) if e.step is Step.AUDIO]


async def test_every_rendered_variant_gets_sound_before_simulation(world: World) -> None:
    world.sound = FakeSoundFinisher()

    record = await world.pipeline().run(world.project_id)

    paths = world.store.paths(world.project_id)
    assert record.state is RunState.DONE
    assert sorted(world.sound.calls) == ["A", "B", "C"]
    for variant in ("A", "B", "C"):
        assert paths.final_video(variant).is_file()
        assert paths.video(variant).read_bytes() == f"video-{variant}".encode()
        sound = world.store.read(paths.sound(variant), SoundRecord)
        tested = next(v for v in record.variants if v.variant_id == variant)
        assert sound.final_video_sha256 == tested.video_sha256
        assert sound.tested_video_sha256 != tested.video_sha256


async def test_the_activity_log_shows_the_sound_step_per_variant(world: World) -> None:
    world.sound = FakeSoundFinisher()

    await world.pipeline().run(world.project_id)

    statuses = [(e.variant_id, e.status) for e in sound_events(world)]
    assert (None, StepStatus.STARTED) in statuses
    assert ("A", StepStatus.SUCCEEDED) in statuses
    assert statuses[-1] == (None, StepStatus.SUCCEEDED)


async def test_a_sound_failure_is_skipped_and_the_run_still_finishes(world: World) -> None:
    world.sound = FakeSoundFinisher()
    world.sound.failures.always("B", SoundError("ffmpeg is missing"))

    record = await world.pipeline().run(world.project_id)

    paths = world.store.paths(world.project_id)
    assert record.state is RunState.DONE
    assert not paths.final_video("B").exists()
    assert paths.final_video("A").is_file()
    skipped = [e for e in sound_events(world) if e.status is StepStatus.SKIPPED]
    assert [e.variant_id for e in skipped] == ["B"]
    assert "silent video" in skipped[0].message


async def test_a_lost_voice_pauses_the_run_and_a_rerun_resumes_with_it(world: World) -> None:
    world.sound = FakeSoundFinisher()
    world.sound.failures.always("B", NarrationError("Narration failed: spending cap"))

    paused = await world.pipeline().run(world.project_id)

    assert paused.state is RunState.FAILED
    assert paused.failed_after is RunState.RENDERED
    assert "run it again to resume with the voice" in (paused.error or "")
    world.sound = _recovered(world.sound)
    resumed = await world.pipeline().run(world.project_id)

    assert resumed.state is RunState.DONE
    assert world.sound.calls.count("A") == 1
    assert world.sound.calls.count("B") == 2


async def test_a_resumed_run_does_not_repeat_finished_sound(world: World) -> None:
    world.sound = FakeSoundFinisher()
    world.sound.failures.always("C", SoundError("transient hiccup"))
    await world.pipeline().run(world.project_id)
    assert sorted(world.sound.calls) == ["A", "B", "C"]

    paths = world.store.paths(world.project_id)
    run = world.store.read(paths.run, RunRecord)
    world.store.write(paths.run, run.model_copy(update={"state": RunState.RENDERED}))
    world.sound = _recovered(world.sound)
    await world.pipeline().run(world.project_id)

    assert world.sound.calls.count("A") == 1
    assert world.sound.calls.count("B") == 1
    assert world.sound.calls.count("C") == 2


def _recovered(finisher: FakeSoundFinisher) -> FakeSoundFinisher:
    """The same finisher (same call log) with its scripted failures used up."""
    finisher.failures = Failures()
    return finisher


async def test_a_cut_that_lost_its_voice_is_retried_once(world: World) -> None:
    world.sound = FakeSoundFinisher()
    world.sound.voiceless["B"] = 1

    await world.pipeline().run(world.project_id)

    paths = world.store.paths(world.project_id)
    assert world.sound.calls.count("B") == 2
    assert all(world.store.read(paths.sound(v), SoundRecord).narrated for v in ("A", "B", "C"))


async def test_if_one_cut_stays_silent_every_cut_drops_the_voice(world: World) -> None:
    world.sound = FakeSoundFinisher()
    world.sound.voiceless["B"] = 2

    record = await world.pipeline().run(world.project_id)

    paths = world.store.paths(world.project_id)
    sounds = [world.store.read(paths.sound(v), SoundRecord) for v in ("A", "B", "C")]
    assert record.state is RunState.DONE
    assert not any(s.narrated for s in sounds)
    assert all("keep the comparison fair" in (s.note or "") for s in sounds)
    for sound in sounds:
        tested = next(v for v in record.variants if v.variant_id == sound.variant_id)
        assert tested.video_sha256 == sound.final_video_sha256
        assert paths.final_video(sound.variant_id).is_file()


async def test_without_a_finisher_there_is_no_sound_step(world: World) -> None:
    await world.pipeline().run(world.project_id)

    assert sound_events(world) == []
