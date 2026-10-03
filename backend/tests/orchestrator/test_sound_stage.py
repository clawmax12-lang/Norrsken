"""Sound is an enhancement: it covers the exported videos, resumes, and never fails the run."""

from preflight.contracts import RunRecord, RunState, SoundRecord, Step, StepStatus
from preflight.errors import SoundError
from tests.orchestrator.fakes import Failures, FakeSoundFinisher, World


def sound_events(world: World):
    return [e for e in world.store.read_events(world.project_id) if e.step is Step.AUDIO]


async def test_winner_and_runner_up_get_sound_and_the_silent_render_is_kept(world: World) -> None:
    world.sound = FakeSoundFinisher()

    record = await world.pipeline().run(world.project_id)

    paths = world.store.paths(world.project_id)
    assert record.state is RunState.DONE
    assert sorted(world.sound.calls) == ["B", "C"]  # ranking order is B, C, A
    for variant in ("B", "C"):
        assert paths.final_video(variant).is_file()
        assert paths.video(variant).read_bytes() == f"video-{variant}".encode()
        sound = world.store.read(paths.sound(variant), SoundRecord)
        tested = next(v for v in record.variants if v.variant_id == variant)
        assert sound.tested_video_sha256 == tested.video_sha256
    assert not paths.final_video("A").exists()


async def test_the_activity_log_shows_the_sound_step_per_variant(world: World) -> None:
    world.sound = FakeSoundFinisher()

    await world.pipeline().run(world.project_id)

    statuses = [(e.variant_id, e.status) for e in sound_events(world)]
    assert (None, StepStatus.STARTED) in statuses
    assert ("B", StepStatus.SUCCEEDED) in statuses
    assert statuses[-1] == (None, StepStatus.SUCCEEDED)


async def test_a_sound_failure_is_skipped_and_the_run_still_finishes(world: World) -> None:
    world.sound = FakeSoundFinisher()
    world.sound.failures.always("B", SoundError("ffmpeg is missing"))

    record = await world.pipeline().run(world.project_id)

    paths = world.store.paths(world.project_id)
    assert record.state is RunState.DONE
    assert not paths.final_video("B").exists()
    assert paths.final_video("C").is_file()
    skipped = [e for e in sound_events(world) if e.status is StepStatus.SKIPPED]
    assert [e.variant_id for e in skipped] == ["B"]
    assert "silent video" in skipped[0].message


async def test_a_resumed_run_does_not_repeat_finished_sound(world: World) -> None:
    world.sound = FakeSoundFinisher()
    world.sound.failures.always("C", SoundError("transient hiccup"))
    await world.pipeline().run(world.project_id)
    assert sorted(world.sound.calls) == ["B", "C"]

    # Re-open the run at EXPLAINED (as if the process died before DONE) and run again.
    paths = world.store.paths(world.project_id)
    run = world.store.read(paths.run, RunRecord)
    world.store.write(paths.run, run.model_copy(update={"state": RunState.EXPLAINED}))
    world.sound = _recovered(world.sound)
    await world.pipeline().run(world.project_id)

    assert world.sound.calls.count("B") == 1  # already finished for this exact render
    assert world.sound.calls.count("C") == 2  # it had been skipped, so it is retried


def _recovered(finisher: FakeSoundFinisher) -> FakeSoundFinisher:
    """The same finisher (same call log) with its scripted failures used up."""
    finisher.failures = Failures()
    return finisher


async def test_without_a_finisher_there_is_no_sound_step(world: World) -> None:
    await world.pipeline().run(world.project_id)

    assert sound_events(world) == []
