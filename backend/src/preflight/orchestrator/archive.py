"""Persisted ``SimulationResult`` files and the rule for which simulators may be scored."""

from collections.abc import Sequence

from preflight.contracts import SimulationResult, SimulatorName, VariantRecord
from preflight.storage import ProjectPaths, ProjectStore


class SimulationArchive:
    """Reads and writes ``simulations/{variant}.{simulator}.json`` for one project."""

    def __init__(
        self, store: ProjectStore, paths: ProjectPaths, simulators: Sequence[SimulatorName]
    ) -> None:
        """Archive results of the configured ``simulators``."""
        self._store = store
        self._paths = paths
        self._simulators = tuple(simulators)

    def save(self, result: SimulationResult) -> None:
        """Persist one result."""
        path = self._paths.simulation(result.variant_id, result.simulator.value)
        self._store.write(path, result)

    def load(self, variant: VariantRecord, simulator: SimulatorName) -> SimulationResult | None:
        """Return the stored result, or ``None`` when absent or computed for other video bytes.

        A prediction is never reused for a video whose hash changed (PRD §9.1).
        """
        path = self._paths.simulation(variant.variant_id, simulator.value)
        if not path.exists():
            return None
        result = self._store.read(path, SimulationResult)
        return result if result.video_sha256 == variant.video_sha256 else None

    def scoring_results(self, variants: Sequence[VariantRecord]) -> tuple[SimulationResult, ...]:
        """Results of every simulator that covers all ``variants``, simulator by simulator.

        A simulator missing even one variant is left out entirely so that variants are only
        ever compared on evidence every one of them has.
        """
        per_simulator = (self._covering(variants, name) for name in self._simulators)
        return tuple(r for results in per_simulator for r in results)

    def _covering(
        self, variants: Sequence[VariantRecord], simulator: SimulatorName
    ) -> tuple[SimulationResult, ...]:
        loaded = tuple(self.load(variant, simulator) for variant in variants)
        results = tuple(r for r in loaded if r is not None)
        return results if len(results) == len(variants) else ()
