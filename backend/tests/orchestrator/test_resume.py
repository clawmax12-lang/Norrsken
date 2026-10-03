"""Resumability: a re-run continues after the last completed state without repeating work."""

import pytest

from preflight.contracts import RunRecord, RunState, Step, StepStatus
from preflight.errors import SimulatorUnavailableError
from tests.orchestrator.fakes import Failures, World


async def test_crash_mid_simulation_then_rerun_only_redoes_the_unfinished_work(
    world: World,
) -> None:
    world.gemini.failures.add("B", RuntimeError("worker crashed"))
    paths = world.store.paths(world.project_id)

    with pytest.raises(RuntimeError, match="worker crashed"):
        await world.pipeline().run(world.project_id)
    assert world.store.read(paths.run, RunRecord).state is RunState.RENDERED

    record = await world.pipeline().run(world.project_id)

    assert record.state is RunState.DONE
    assert world.planner.calls == 1
    assert sorted(world.renderer.calls) == ["A", "B", "C"]
    assert world.composer.calls == ["A", "B", "C"] or sorted(world.composer.calls) == [
        "A",
        "B",
        "C",
    ]
    assert sorted(world.gemini.calls) == ["A", "B", "B", "C"]
    assert world.explainer.calls.count("B") == 1


async def test_resumed_stages_are_logged_as_skipped(world: World) -> None:
    world.gemini.failures.add("B", RuntimeError("worker crashed"))
    with pytest.raises(RuntimeError):
        await world.pipeline().run(world.project_id)

    await world.pipeline().run(world.project_id)

    skipped = [
        e.step
        for e in world.store.read_events(world.project_id)
        if e.status is StepStatus.SKIPPED and e.variant_id is None
    ]
    assert skipped == [Step.PLAN, Step.RENDER]


async def test_crash_is_logged_as_a_failed_step(world: World) -> None:
    world.gemini.failures.add("B", RuntimeError("worker crashed"))
    with pytest.raises(RuntimeError):
        await world.pipeline().run(world.project_id)

    failed = [e for e in world.store.read_events(world.project_id) if e.status is StepStatus.FAILED]
    assert {e.step for e in failed} == {Step.SIMULATE}
    assert any("worker crashed" in e.message for e in failed)


async def test_failed_run_resumes_from_the_last_completed_state(world: World) -> None:
    world.gemini.failures.always("A", SimulatorUnavailableError("down"))
    world.gemini.failures.always("B", SimulatorUnavailableError("down"))
    world.gemini.failures.always("C", SimulatorUnavailableError("down"))
    failed = await world.pipeline().run(world.project_id)
    assert failed.state is RunState.FAILED
    assert failed.failed_after is RunState.RENDERED

    world.gemini.failures = Failures()
    record = await world.pipeline().run(world.project_id)

    assert record.state is RunState.DONE
    assert record.error is None and record.failed_after is None
    assert world.planner.calls == 1
    assert len(world.renderer.calls) == 3
