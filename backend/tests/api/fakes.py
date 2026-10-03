"""Test doubles for the orchestrator seam. They live only in tests."""

import asyncio

from preflight.contracts import ActivityEvent, RunRecord, RunState, Step, StepStatus
from preflight.storage import ProjectStore
from tests.export.seed import NOW


def activity(message: str, step: Step = Step.PLAN, status: StepStatus = StepStatus.STARTED):
    return ActivityEvent(at=NOW, step=step, status=status, message=message)


def set_state(store: ProjectStore, project_id: str, state: RunState, error: str | None = None):
    store.write(
        store.paths(project_id).run,
        RunRecord(project_id=project_id, state=state, error=error, updated_at=NOW),
    )


class FakeRunService:
    """Logs two events, waits for ``release``, then finishes the run as DONE."""

    def __init__(self, store: ProjectStore) -> None:
        self._store = store
        self.calls: list[str] = []
        self.started = asyncio.Event()
        self.release = asyncio.Event()

    async def run(self, project_id: str) -> RunRecord:
        self.calls.append(project_id)
        self._store.append_event(project_id, activity("planning"))
        self.started.set()
        await self.release.wait()
        self._store.append_event(project_id, activity("planned", status=StepStatus.SUCCEEDED))
        set_state(self._store, project_id, RunState.DONE)
        return self._store.read(self._store.paths(project_id).run, RunRecord)


class CrashingRunService:
    """Dies the way an unexpected bug would."""

    async def run(self, project_id: str) -> RunRecord:
        raise RuntimeError("renderer exploded")
