"""FR-06/FR-08: concrete "what to change next time" lines, grounded in the weakest moment."""

from collections.abc import Sequence

from preflight.contracts import Confidence, CreativeConcept, Ranking, SimulationResult

from .moments import Moment, variant_results, weakest_moment
from .wording import format_range, simulator_label

MAX_SUGGESTIONS = 3


def next_time_suggestions(
    concept: CreativeConcept, ranking: Ranking, results: Sequence[SimulationResult]
) -> tuple[str, ...]:
    """Return 1-3 changes to try next time, each tied to the concept's own scenes and copy.

    The first names the scene on screen at the weakest moment. A second reworks the hook or
    call to action when that moment falls in the opening or closing scene. A last one says
    the order is a hypothesis to A/B test when ``ranking`` has low confidence.

    Raises:
        PreflightValidationError: If ``results`` has nothing usable for the variant.
    """
    own = variant_results(concept, results)
    weakest = weakest_moment(own, concept.duration_s)
    suggestions = [_shorten_weakest_scene(concept, weakest)]
    suggestions += _rework_opening_or_closing(concept, weakest)
    if ranking.confidence is Confidence.LOW:
        suggestions.append(
            "The ranking has low confidence (one simulator, or the simulators disagree): "
            "treat the winner as a hypothesis and A/B test it before committing."
        )
    return tuple(suggestions[:MAX_SUGGESTIONS])


def _shorten_weakest_scene(concept: CreativeConcept, weakest: Moment) -> str:
    scene = concept.scene_at(weakest.t)
    span = format_range(scene.t_start, scene.t_end)
    simulator = simulator_label(weakest.simulator)
    if weakest.reported:
        finding = (
            f"Simulated viewers dropped on '{scene.text}' ({span}, {simulator}: {weakest.detail})"
        )
    else:
        finding = f"The {simulator} series was weakest on '{scene.text}' ({span})"
    return f"{finding}: shorten this scene or tighten its wording."


def _rework_opening_or_closing(concept: CreativeConcept, weakest: Moment) -> list[str]:
    scene = concept.scene_at(weakest.t)
    if scene is concept.scenes[0]:
        return [
            f"The weakest moment is in the opening scene: rework the hook "
            f"'{concept.hook}' (from {concept.hook_source_field.value})."
        ]
    if scene is concept.scenes[-1]:
        return [
            f"The weakest moment is in the closing scene: rework the call to action "
            f"'{concept.cta}' (from {concept.cta_source_field.value})."
        ]
    return []
