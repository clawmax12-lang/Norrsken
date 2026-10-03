"""The happy path, the artifacts it leaves behind and the order of the activity log."""

import pytest

from preflight.contracts import (
    ActivityEvent,
    Ranking,
    RenderStatus,
    Report,
    RunRecord,
    RunState,
    SimulatorName,
    Step,
    StepStatus,
)
from preflight.errors import StorageError
from tests.orchestrator.fakes import VARIANTS, FakeSimulator, World


def events(world: World) -> list[ActivityEvent]:
    return list(world.store.read_events(world.project_id))


async def test_happy_path_reaches_done_and_persists_every_artifact(world: World) -> None:
    record = await world.pipeline().run(world.project_id)

    paths = world.store.paths(world.project_id)
    assert record.state is RunState.DONE
    assert world.store.read(paths.run, RunRecord) == record
    for variant in VARIANTS:
        assert paths.concept(variant).is_file()
        assert paths.spec(variant).is_file()
        assert paths.video(variant).is_file()
        assert paths.simulation(variant, "gemini_panel").is_file()
    assert paths.ranking.is_file()
    assert paths.report.is_file()


async def test_report_names_winner_runner_up_reasons_and_measured_savings(world: World) -> None:
    await world.pipeline().run(world.project_id)

    paths = world.store.paths(world.project_id)
    report = world.store.read(paths.report, Report)
    ranking = world.store.read(paths.ranking, Ranking)
    assert ranking.order == ("B", "C", "A")
    assert (report.winner, report.runner_up) == ("B", "C")
    assert set(report.reasons) == set(VARIANTS)
    assert report.next_time == ("Try a stronger hook",)
    assert report.token_savings.tokens_saved == 400
    assert report.brain_sim is False


async def test_brain_sim_is_true_only_when_tribe_results_were_scored(world: World) -> None:
    world.extra_simulators.append(FakeSimulator(SimulatorName.TRIBE_V2))

    await world.pipeline().run(world.project_id)

    report = world.store.read(world.store.paths(world.project_id).report, Report)
    assert report.brain_sim is True


async def test_every_variant_is_recorded_as_rendered_with_its_render_time(world: World) -> None:
    record = await world.pipeline().run(world.project_id)

    assert [v.variant_id for v in record.variants] == list(VARIANTS)
    for variant in record.variants:
        assert variant.render_status is RenderStatus.RENDERED
        assert variant.video_path == f"videos/{variant.variant_id}.mp4"
        assert variant.render_seconds == 2.5


async def test_each_stage_logs_started_then_succeeded_in_state_machine_order(world: World) -> None:
    await world.pipeline().run(world.project_id)

    stage_events = [e for e in events(world) if e.variant_id is None]
    assert [(e.step, e.status) for e in stage_events] == [
        (step, status)
        for step in (Step.PLAN, Step.RENDER, Step.SIMULATE, Step.SCORE, Step.EXPLAIN)
        for status in (StepStatus.STARTED, StepStatus.SUCCEEDED)
    ]
    finished = [e for e in stage_events if e.status is StepStatus.SUCCEEDED]
    assert all(e.duration_s and e.duration_s > 0 for e in finished)
    assert [e.at for e in stage_events] == sorted(e.at for e in stage_events)


async def test_render_time_is_logged_per_video(world: World) -> None:
    await world.pipeline().run(world.project_id)

    renders = [
        e
        for e in events(world)
        if e.step is Step.RENDER and e.variant_id and e.status is StepStatus.SUCCEEDED
    ]
    assert sorted(e.variant_id or "" for e in renders) == list(VARIANTS)
    assert all("in 2.5s" in e.message and e.duration_s is not None for e in renders)


async def test_renders_run_concurrently_but_never_more_than_two_at_once(world: World) -> None:
    await world.pipeline().run(world.project_id)

    assert world.renderer.max_in_flight == 2


async def test_running_a_finished_project_again_does_nothing(world: World) -> None:
    pipeline = world.pipeline()
    first = await pipeline.run(world.project_id)
    logged = len(events(world))

    second = await pipeline.run(world.project_id)

    assert second == first
    assert len(events(world)) == logged
    assert world.planner.calls == 1


async def test_a_project_without_a_brief_fails_loudly(world: World) -> None:
    world.store.paths(world.project_id).brief.unlink()

    with pytest.raises(StorageError):
        await world.pipeline().run(world.project_id)
