"""Starting runs in the background without owning how a run works."""

import asyncio
import logging
from typing import Protocol

from preflight.contracts import RunRecord, RunState
from preflight.ports import Clock
from preflight.storage import ProjectStore

logger = logging.getLogger(__name__)


class RunService(Protocol):
    """What the API needs from the orchestrator: run a project to a terminal state.

    The orchestrator's pipeline satisfies this. It persists progress and the activity log
    itself and returns the final record; the API only schedules it and reports on it.
    """

    async def run(self, project_id: str) -> RunRecord:
        """Run ``project_id`` from its last completed state and return the final record."""
        ...


class RunTracker:
    """Runs each project at most once at a time, in the background of the web process.

    Runs live in this process only. A second request for a project that is already running is
    a no-op, which makes ``POST /run`` safe to retry. If a run dies with an unexpected error
    the project is marked ``FAILED`` so streams of its log end instead of waiting forever.
    """

    def __init__(self, store: ProjectStore, service: RunService, clock: Clock) -> None:
        """Track runs of ``service`` and record crashes in ``store``."""
        self._store = store
        self._service = service
        self._clock = clock
        self._tasks: dict[str, asyncio.Task[None]] = {}

    def is_running(self, project_id: str) -> bool:
        """True while a run for ``project_id`` is in flight."""
        return project_id in self._tasks

    def start(self, project_id: str) -> bool:
        """Start a run unless one is in flight; return whether a new run was started."""
        if self.is_running(project_id):
            return False
        self._tasks[project_id] = asyncio.create_task(self._supervise(project_id))
        return True

    async def shutdown(self) -> None:
        """Cancel in-flight runs when the server stops."""
        tasks = list(self._tasks.values())
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _supervise(self, project_id: str) -> None:
        try:
            await self._service.run(project_id)
        except Exception as exc:
            logger.exception("run for project %s crashed", project_id)
            await asyncio.to_thread(self._mark_failed, project_id, exc)
        finally:
            self._tasks.pop(project_id, None)

    def _mark_failed(self, project_id: str, exc: Exception) -> None:
        paths = self._store.paths(project_id)
        record = self._store.read(paths.run, RunRecord)
        if record.state in (RunState.DONE, RunState.FAILED):
            return
        failed = record.model_copy(
            update={
                "state": RunState.FAILED,
                "error": f"run crashed: {type(exc).__name__}: {exc}",
                "failed_after": record.state,
                "updated_at": self._clock(),
            }
        )
        self._store.write(paths.run, failed)
