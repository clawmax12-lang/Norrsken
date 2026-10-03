"""Everything a stage needs about the run in progress, bundled so stages stay small."""

from dataclasses import dataclass

from preflight.contracts import Brief, CreativeConcept, RenderStatus, VariantRecord
from preflight.storage import ProjectPaths, ProjectStore

from .activity import ActivityLog
from .archive import SimulationArchive
from .tracker import RunTracker


@dataclass(frozen=True)
class RunContext:
    """One project's brief, storage, activity log, state tracker and simulation archive."""

    store: ProjectStore
    paths: ProjectPaths
    brief: Brief
    log: ActivityLog
    tracker: RunTracker
    archive: SimulationArchive

    def read_concept(self, variant_id: str) -> CreativeConcept:
        """Load the persisted concept of ``variant_id``."""
        return self.store.read(self.paths.concept(variant_id), CreativeConcept)

    def rendered_variants(self) -> tuple[VariantRecord, ...]:
        """Variants whose render succeeded, ordered by variant id."""
        return tuple(
            v for v in self.tracker.record.variants if v.render_status is RenderStatus.RENDERED
        )
