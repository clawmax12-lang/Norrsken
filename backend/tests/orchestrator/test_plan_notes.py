"""What the planner noticed about the brief reaches the activity log and the report."""

from preflight.contracts import PlanNotes, Report, Step, StepStatus
from tests.orchestrator.fakes import World

SHOPIFY = "Screenshot 3 shows Shopify, not Acme Notes; it was left out of every video."


async def test_plan_notes_are_logged_and_lead_the_next_time_list(world: World) -> None:
    world.planner.last_notes = PlanNotes(excluded_screenshots=(2,), messages=(SHOPIFY,))  # type: ignore[attr-defined]

    await world.pipeline().run(world.project_id)

    paths = world.store.paths(world.project_id)
    assert world.store.read(paths.plan_notes, PlanNotes).excluded_screenshots == (2,)
    report = world.store.read(paths.report, Report)
    assert report.next_time[0] == SHOPIFY
    logged = [
        e
        for e in world.store.read_events(world.project_id)
        if e.step is Step.PLAN and e.status is StepStatus.SKIPPED
    ]
    assert [e.message for e in logged] == [SHOPIFY]


async def test_a_planner_without_notes_leaves_the_report_unchanged(world: World) -> None:
    await world.pipeline().run(world.project_id)

    paths = world.store.paths(world.project_id)
    assert not paths.plan_notes.exists()
    report = world.store.read(paths.report, Report)
    assert report.next_time == ("Try a stronger hook",)
    assert report.production is None


async def test_a_soft_screen_caps_the_reported_score(world: World) -> None:
    world.planner.last_notes = PlanNotes(smallest_screen_px=284)  # type: ignore[attr-defined]

    await world.pipeline().run(world.project_id)

    report = world.store.read(world.store.paths(world.project_id).report, Report)
    assert report.production is not None
    assert report.production.factor == 0.5
    assert "284 px" in report.production.reasons[0]
