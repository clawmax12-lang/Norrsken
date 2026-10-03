"""FR-06: the deterministic explainer. No LLM is involved, so every reason is reproducible."""

from collections.abc import Sequence

from preflight.contracts import Brief, CreativeConcept, Ranking, Reason, SimulationResult

from .moments import Moment, select_moments, variant_results
from .wording import format_timestamp, scene_label, simulator_label


class RuleBasedExplainer:
    """Explains a variant from the hold and drop moments its simulators reported.

    Implements :class:`preflight.ports.Explainer`. Each reason names the scene on screen at
    that second, quotes its text and says which simulator the moment comes from. When fewer
    than two distinct moments were reported, it derives them from the primary series and
    says so in the text.
    """

    async def explain(
        self,
        brief: Brief,  # noqa: ARG002 - part of the Explainer port; this explainer needs only the scenes
        concept: CreativeConcept,
        ranking: Ranking,  # noqa: ARG002 - reasons describe moments, whatever the variant's rank
        results: Sequence[SimulationResult],
    ) -> tuple[Reason, ...]:
        """Return 2-4 reasons, sorted by time, each tied to a real scene of ``concept``.

        Raises:
            PreflightValidationError: If ``results`` has nothing usable for the variant.
        """
        own = variant_results(concept, results)
        return tuple(_reason(concept, moment) for moment in select_moments(own, concept.duration_s))


def _reason(concept: CreativeConcept, moment: Moment) -> Reason:
    scene = concept.scene_at(moment.t)
    index = concept.scenes.index(scene)
    text = (
        f"{moment.kind.value} at {format_timestamp(moment.t)} ({scene_label(index, scene)}): "
        f"{moment.detail} ({_provenance(moment)})"
    )
    return Reason(t=moment.t, scene_index=index, text=text)


def _provenance(moment: Moment) -> str:
    simulator = simulator_label(moment.simulator)
    if moment.reported:
        return f"reported by the {simulator}"
    return (
        f"derived from the {simulator} series because fewer than two distinct "
        "hold or drop moments were reported"
    )
