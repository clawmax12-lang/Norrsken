"""FR-06/FR-08: concrete "what to change next time" lines, grounded in the weakest moment."""

from collections.abc import Sequence

from preflight.advice import advice
from preflight.contracts import Confidence, CreativeConcept, Ranking, Scene, SimulationResult

from .moments import Moment, variant_results, weakest_moment
from .wording import format_range

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
        suggestions.append(advice("low_confidence", concept.language))
    return tuple(suggestions[:MAX_SUGGESTIONS])


def _shorten_weakest_scene(concept: CreativeConcept, weakest: Moment) -> str:
    scene = concept.scene_at(weakest.t)
    span = format_range(scene.t_start, scene.t_end)
    simulator = advice(f"sim_{weakest.simulator.value}", concept.language)
    text = _on_screen(concept, scene)
    if weakest.reported:
        return advice(
            "weakest_reported",
            concept.language,
            text=text,
            span=span,
            simulator=simulator,
            detail=weakest.detail,
        )
    return advice("weakest_series", concept.language, text=text, span=span, simulator=simulator)


def _on_screen(concept: CreativeConcept, scene: Scene) -> str:
    """The copy viewers read in ``scene``: the hook opens the video and the button closes it."""
    if scene is concept.scenes[0]:
        return concept.hook
    if scene is concept.scenes[-1]:
        return concept.cta
    return scene.text


def _rework_opening_or_closing(concept: CreativeConcept, weakest: Moment) -> list[str]:
    scene = concept.scene_at(weakest.t)
    if scene is concept.scenes[0]:
        field = concept.hook_source_field.value
        return [advice("rework_hook", concept.language, hook=concept.hook, field=field)]
    if scene is concept.scenes[-1]:
        field = concept.cta_source_field.value
        return [advice("rework_cta", concept.language, cta=concept.cta, field=field)]
    return []
