"""FR-09: the append-only activity log, written through the project store.

Every step appends a ``STARTED`` line and then exactly one of ``SUCCEEDED``, ``FAILED`` or
``SKIPPED``, each stamped by the injected clock so tests and replays are deterministic.
"""

import logging
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime

from preflight.contracts import ActivityEvent, Step, StepStatus
from preflight.ports import Clock
from preflight.storage import ProjectStore

_LOG = logging.getLogger(__name__)


@dataclass
class StepHandle:
    """Lets a running step choose the line it is reported with when it finishes."""

    message: str
    status: StepStatus = StepStatus.SUCCEEDED

    def report(self, message: str) -> None:
        """Replace the success message, for example to include a measured render time."""
        self.message = message

    def skip(self, message: str) -> None:
        """Finish as ``SKIPPED``: the step degraded gracefully instead of failing."""
        self.message = message
        self.status = StepStatus.SKIPPED


class ActivityLog:
    """Writes one project's activity events (``log.jsonl``) and measures step durations."""

    def __init__(self, store: ProjectStore, project_id: str, clock: Clock) -> None:
        """Log into ``project_id`` using ``clock`` for timestamps and durations."""
        self._store = store
        self._project_id = project_id
        self._clock = clock

    @contextmanager
    def step(
        self, step: Step, title: str, *, variant_id: str | None = None
    ) -> Iterator[StepHandle]:
        """Log ``STARTED``, then ``SUCCEEDED``/``SKIPPED`` with a duration, or ``FAILED``.

        Exceptions are logged and re-raised: the log observes failures, it never hides them.
        """
        started = self._emit(step, StepStatus.STARTED, title, variant_id)
        handle = StepHandle(message=f"{title}: done")
        try:
            yield handle
        except Exception as exc:
            reason = str(exc) or type(exc).__name__
            self._emit(step, StepStatus.FAILED, f"{title} failed: {reason}", variant_id, started)
            raise
        self._emit(step, handle.status, handle.message, variant_id, started)

    def skipped(self, step: Step, message: str, *, variant_id: str | None = None) -> None:
        """Log a step that did not need to run (already complete, or intentionally dropped)."""
        self._emit(step, StepStatus.SKIPPED, message, variant_id)

    def _emit(
        self,
        step: Step,
        status: StepStatus,
        message: str,
        variant_id: str | None,
        since: datetime | None = None,
    ) -> datetime:
        at = self._clock()
        duration = None if since is None else max((at - since).total_seconds(), 0.0)
        event = ActivityEvent(
            at=at,
            step=step,
            status=status,
            message=message,
            variant_id=variant_id,
            duration_s=duration,
        )
        self._store.append_event(self._project_id, event)
        _LOG.info("%s %s %s (%s)", self._project_id, step.value, status.value, message)
        return at
