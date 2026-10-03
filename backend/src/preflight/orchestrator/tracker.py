"""``run.json``: the persisted state machine position and per-variant progress (PRD §9)."""

from dataclasses import dataclass
from typing import Self

from preflight.contracts import RunRecord, RunState, VariantRecord
from preflight.ports import Clock
from preflight.storage import ProjectPaths, ProjectStore

_ORDER = (
    RunState.BRIEF_RECEIVED,
    RunState.PLANNED,
    RunState.RENDERED,
    RunState.SIMULATED,
    RunState.SCORED,
    RunState.EXPLAINED,
    RunState.DONE,
)


@dataclass
class RunTracker:
    """Owns the run's :class:`RunRecord` and persists every change before it is observable."""

    store: ProjectStore
    paths: ProjectPaths
    clock: Clock
    record: RunRecord

    @classmethod
    def open(cls, store: ProjectStore, project_id: str, clock: Clock) -> Self:
        """Load ``run.json`` or start at ``BRIEF_RECEIVED``; a ``FAILED`` run is reopened.

        Reopening moves a failed run back to the last state it completed, which is what makes
        a re-run resume instead of starting over.
        """
        paths = store.paths(project_id)
        if paths.run.exists():
            tracker = cls(store, paths, clock, store.read(paths.run, RunRecord))
            tracker._reopen_if_failed()
            return tracker
        fresh = RunRecord(project_id=project_id, state=RunState.BRIEF_RECEIVED, updated_at=clock())
        tracker = cls(store, paths, clock, fresh)
        tracker._save(fresh)
        return tracker

    def has_completed(self, state: RunState) -> bool:
        """True when the run has already passed ``state``."""
        return _ORDER.index(state) <= _ORDER.index(self.record.state)

    def advance(self, state: RunState) -> None:
        """Record that ``state`` is complete."""
        self._update(state=state)

    def set_variants(self, variants: tuple[VariantRecord, ...]) -> None:
        """Replace the variant list, ordered by variant id."""
        self._update(variants=tuple(sorted(variants, key=lambda v: v.variant_id)))

    def update_variant(self, variant: VariantRecord) -> None:
        """Replace one variant's record and persist immediately (renders finish one by one)."""
        others = tuple(v for v in self.record.variants if v.variant_id != variant.variant_id)
        self.set_variants((*others, variant))

    def fail(self, error: Exception) -> None:
        """Mark the run ``FAILED``, remembering the state to resume from."""
        self._update(state=RunState.FAILED, error=str(error), failed_after=self.record.state)

    def _reopen_if_failed(self) -> None:
        if self.record.state is RunState.FAILED:
            resume = self.record.failed_after or RunState.BRIEF_RECEIVED
            self._update(state=resume, error=None, failed_after=None)

    def _update(self, **changes: object) -> None:
        self._save(self.record.model_copy(update={**changes, "updated_at": self.clock()}))

    def _save(self, record: RunRecord) -> None:
        self.record = record
        self.store.write(self.paths.run, record)
