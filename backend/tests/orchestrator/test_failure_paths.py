"""Retry, timeout, render failure, simulator outage and the survivor edge cases."""

from preflight.contracts import (
    ActivityEvent,
    Ranking,
    RenderStatus,
    Report,
    RunState,
    SimulatorName,
    Step,
    StepStatus,
)
from preflight.errors import (
    ProviderError,
    RenderError,
    SimulatorUnavailableError,
    TransientProviderError,
)
from tests.orchestrator.fakes import FakeSimulator, World


def events(world: World) -> list[ActivityEvent]:
    return list(world.store.read_events(world.project_id))


async def test_one_transient_planner_error_is_retried_once(world: World) -> None:
    world.planner.failures.add("plan", TransientProviderError("429"))

    record = await world.pipeline().run(world.project_id)

    assert record.state is RunState.DONE
    assert world.planner.calls == 2


async def test_a_second_transient_error_fails_the_run_with_the_reason(world: World) -> None:
    world.planner.failures.add("plan", TransientProviderError("429"), TransientProviderError("429"))

    record = await world.pipeline().run(world.project_id)

    assert record.state is RunState.FAILED
    assert record.failed_after is RunState.BRIEF_RECEIVED
    assert record.error == "429"
    assert world.planner.calls == 2


async def test_a_non_transient_provider_error_is_not_retried(world: World) -> None:
    world.planner.failures.add("plan", ProviderError("bad key"))

    record = await world.pipeline().run(world.project_id)

    assert record.state is RunState.FAILED
    assert world.planner.calls == 1


async def test_a_step_that_exceeds_the_timeout_fails_without_a_retry(world: World) -> None:
    world.settings = world.settings.model_copy(update={"step_timeout_s": 0.05})
    world.planner.delay_s = 1.0

    record = await world.pipeline().run(world.project_id)

    assert record.state is RunState.FAILED
    assert record.error is not None and "timed out" in record.error
    assert world.planner.calls == 1


async def test_a_planner_returning_the_wrong_number_of_concepts_fails(world: World) -> None:
    world.planner.concepts = world.planner.concepts[:2]

    record = await world.pipeline().run(world.project_id)

    assert record.state is RunState.FAILED
    assert record.error is not None and "3 concepts" in record.error


async def test_a_failed_render_is_retried_once_then_marked_failed_without_stopping(
    world: World,
) -> None:
    world.renderer.failures.always("B", RenderError("ffmpeg crashed"))

    record = await world.pipeline().run(world.project_id)

    assert record.state is RunState.DONE
    assert world.renderer.calls.count("B") == 2
    failed = {v.variant_id: v for v in record.variants}["B"]
    assert failed.render_status is RenderStatus.FAILED
    assert failed.error == "ffmpeg crashed"
    ranking = world.store.read(world.store.paths(world.project_id).ranking, Ranking)
    assert ranking.order == ("C", "A")
    assert ranking.excluded == {"B": "ffmpeg crashed"}


async def test_a_render_that_succeeds_on_retry_is_rendered(world: World) -> None:
    world.renderer.failures.add("B", RenderError("flaky"))

    record = await world.pipeline().run(world.project_id)

    assert {v.render_status for v in record.variants} == {RenderStatus.RENDERED}


async def test_one_surviving_variant_is_ranked_alone_without_a_runner_up(world: World) -> None:
    world.renderer.failures.always("A", RenderError("boom"))
    world.renderer.failures.always("B", RenderError("boom"))

    record = await world.pipeline().run(world.project_id)

    paths = world.store.paths(world.project_id)
    report = world.store.read(paths.report, Report)
    assert record.state is RunState.DONE
    assert (report.winner, report.runner_up) == ("C", None)
    assert set(world.store.read(paths.ranking, Ranking).excluded) == {"A", "B"}
    score_line = next(e for e in events(world) if e.step is Step.SCORE and e.duration_s)
    assert "no runner-up" in score_line.message


async def test_no_surviving_variant_fails_clearly_and_writes_no_ranking(world: World) -> None:
    for variant in "ABC":
        world.renderer.failures.always(variant, RenderError("boom"))

    record = await world.pipeline().run(world.project_id)

    assert record.state is RunState.FAILED
    assert record.error == "no variant rendered successfully"
    assert not world.store.paths(world.project_id).ranking.exists()


async def test_an_unavailable_simulator_is_dropped_and_the_run_continues(world: World) -> None:
    tribe = FakeSimulator(SimulatorName.TRIBE_V2)
    for variant in "ABC":
        tribe.failures.always(variant, SimulatorUnavailableError("no GPU worker"))
    world.extra_simulators.append(tribe)

    record = await world.pipeline().run(world.project_id)

    report = world.store.read(world.store.paths(world.project_id).report, Report)
    assert record.state is RunState.DONE
    assert report.brain_sim is False
    messages = [e.message for e in events(world) if e.status is not StepStatus.STARTED]
    assert any("no GPU worker" in m for m in messages)
    assert any("tribe_v2 left out" in m for m in messages)


async def test_a_simulator_missing_one_variant_is_left_out_of_scoring_entirely(
    world: World,
) -> None:
    tribe = FakeSimulator(SimulatorName.TRIBE_V2)
    tribe.failures.always("B", SimulatorUnavailableError("timeout"))
    world.extra_simulators.append(tribe)

    await world.pipeline().run(world.project_id)

    paths = world.store.paths(world.project_id)
    assert world.store.read(paths.report, Report).brain_sim is False
    assert set(world.store.read(paths.ranking, Ranking).per_simulator) == {
        SimulatorName.GEMINI_PANEL
    }


async def test_a_transient_simulator_error_is_retried_once(world: World) -> None:
    world.gemini.failures.add("A", TransientProviderError("503"))

    record = await world.pipeline().run(world.project_id)

    assert record.state is RunState.DONE
    assert world.gemini.calls.count("A") == 2


async def test_no_remaining_simulator_fails_the_run(world: World) -> None:
    for variant in "ABC":
        world.gemini.failures.always(variant, SimulatorUnavailableError("down"))

    record = await world.pipeline().run(world.project_id)

    assert record.state is RunState.FAILED
    assert record.failed_after is RunState.RENDERED
    assert record.error == "no simulator produced results for every rendered variant"


async def test_a_result_for_the_wrong_variant_fails_the_run(world: World) -> None:
    world.gemini.wrong_variant = True

    record = await world.pipeline().run(world.project_id)

    assert record.state is RunState.FAILED
    assert record.error is not None and "does not match" in record.error


async def test_unavailable_asset_generation_falls_back_to_template_backgrounds(
    world: World,
) -> None:
    world.generator.failures.always("generate", ProviderError("quota"))

    record = await world.pipeline().run(world.project_id)

    assert record.state is RunState.DONE
    skipped = [
        e for e in events(world) if e.step is Step.GENERATE and e.status is StepStatus.SKIPPED
    ]
    assert len(skipped) == 3
    assert "template-only" in skipped[0].message


async def test_an_explainer_failure_fails_the_run_after_scoring(world: World) -> None:
    world.explainer.failures.always("explain", ProviderError("quota"))

    record = await world.pipeline().run(world.project_id)

    assert record.state is RunState.FAILED
    assert record.failed_after is RunState.SCORED
    assert not world.store.paths(world.project_id).report.exists()


async def test_a_failing_stage_logs_a_failed_line_with_its_duration(world: World) -> None:
    world.planner.failures.add("plan", ProviderError("bad key"))

    await world.pipeline().run(world.project_id)

    failed = [e for e in events(world) if e.status is StepStatus.FAILED]
    assert [(e.step, e.message) for e in failed] == [
        (Step.PLAN, "Planning concepts failed: bad key")
    ]
    assert failed[0].duration_s is not None
