"""StepPolicy, gather_bounded, ActivityLog and RunTracker on their own."""

import asyncio

import pytest

from preflight.contracts import RunState, Step, StepStatus, VariantRecord
from preflight.errors import ProviderError, RenderError, TransientProviderError
from preflight.orchestrator.activity import ActivityLog
from preflight.orchestrator.concurrency import gather_bounded
from preflight.orchestrator.retry import StepPolicy
from preflight.orchestrator.tracker import RunTracker
from preflight.storage import ProjectStore
from tests.orchestrator.fakes import FakeClock


class Flaky:
    def __init__(self, *errors: Exception) -> None:
        self.errors = list(errors)
        self.calls = 0

    async def __call__(self) -> str:
        self.calls += 1
        if self.errors:
            raise self.errors.pop(0)
        return "ok"


async def test_policy_retries_only_the_configured_errors() -> None:
    policy = StepPolicy(timeout_s=1, retries=1)
    flaky = Flaky(TransientProviderError("x"))
    assert await policy.run(flaky) == "ok"
    assert flaky.calls == 2

    other = Flaky(RenderError("x"))
    with pytest.raises(RenderError):
        await policy.run(other)
    assert other.calls == 1

    render = Flaky(RenderError("x"))
    assert await policy.run(render, retry_on=(RenderError,)) == "ok"


async def test_policy_with_zero_retries_calls_once() -> None:
    flaky = Flaky(TransientProviderError("x"))
    with pytest.raises(TransientProviderError):
        await StepPolicy(timeout_s=1, retries=0).run(flaky)
    assert flaky.calls == 1


async def test_policy_turns_a_timeout_into_a_provider_error() -> None:
    async def hang() -> None:
        await asyncio.sleep(5)

    with pytest.raises(ProviderError, match=r"timed out after 0\.01s"):
        await StepPolicy(timeout_s=0.01, retries=1).run(hang)


async def test_gather_bounded_limits_concurrency_and_keeps_job_order() -> None:
    running = peak = 0

    async def job(value: int) -> int:
        nonlocal running, peak
        running += 1
        peak = max(peak, running)
        await asyncio.sleep(0.01)
        running -= 1
        return value

    results = await gather_bounded(2, [lambda v=v: job(v) for v in range(5)])

    assert results == [0, 1, 2, 3, 4]
    assert peak == 2


async def test_gather_bounded_lets_siblings_finish_before_raising() -> None:
    finished: list[int] = []

    async def job(value: int) -> int:
        await asyncio.sleep(0.01 * value)
        if value == 0:
            raise RuntimeError("boom")
        finished.append(value)
        return value

    with pytest.raises(RuntimeError, match="boom"):
        await gather_bounded(3, [lambda v=v: job(v) for v in range(3)])
    assert finished == [1, 2]


def test_activity_log_records_failures_and_reraises(tmp_path) -> None:  # type: ignore[no-untyped-def]
    store = ProjectStore(tmp_path)
    store.create("p")
    log = ActivityLog(store, "p", FakeClock())

    with pytest.raises(ValueError), log.step(Step.PLAN, "Planning"):
        raise ValueError

    event = list(store.read_events("p"))[-1]
    assert (event.status, event.message, event.duration_s) == (
        StepStatus.FAILED,
        "Planning failed: ValueError",
        1.0,
    )


def test_tracker_persists_every_change_and_reopens_failed_runs(tmp_path) -> None:  # type: ignore[no-untyped-def]
    store = ProjectStore(tmp_path)
    store.create("p")
    clock = FakeClock()
    tracker = RunTracker.open(store, "p", clock)
    tracker.advance(RunState.PLANNED)
    tracker.update_variant(VariantRecord(variant_id="B"))
    tracker.update_variant(VariantRecord(variant_id="A"))
    tracker.fail(ProviderError("down"))

    reopened = RunTracker.open(store, "p", clock)

    assert reopened.record.state is RunState.PLANNED
    assert [v.variant_id for v in reopened.record.variants] == ["A", "B"]
    assert reopened.has_completed(RunState.PLANNED)
    assert not reopened.has_completed(RunState.RENDERED)
