"""Plan-level checks that need the brief: everything the schema alone cannot express (FR-02)."""

from pydantic import ValidationError

from preflight.contracts import Brief, CreativeConcept

from .archetypes import Archetype
from .draft import PlanDraft, assemble_concepts, variant_id
from .grounding import find_violations


def plan_problems(draft: PlanDraft, brief: Brief, archetypes: tuple[Archetype, ...]) -> list[str]:
    """Every reason ``draft`` is unusable, phrased for the model; empty means acceptable."""
    if len(draft.concepts) != len(archetypes):
        return [f"return exactly {len(archetypes)} concepts, not {len(draft.concepts)}"]
    index_problems = _screenshot_index_problems(draft, len(brief.screenshots))
    if index_problems:
        return index_problems
    try:
        concepts = assemble_concepts(draft, brief, archetypes)
    except ValidationError as exc:
        return [f"concept does not satisfy the contract: {error['msg']}" for error in exc.errors()]
    return [*_set_problems(concepts), *_grounding_problems(concepts, brief)]


def _screenshot_index_problems(draft: PlanDraft, screenshot_count: int) -> list[str]:
    return [
        f"concept {variant_id(c)} scene {s}: screenshot_index {scene.screenshot_index} does not "
        f"exist; use 0 to {screenshot_count - 1}"
        for c, concept in enumerate(draft.concepts)
        for s, scene in enumerate(concept.scenes, start=1)
        if scene.screenshot_index >= screenshot_count
    ]


def _set_problems(concepts: tuple[CreativeConcept, ...]) -> list[str]:
    """The invariants of the whole plan: sequential unique ids and distinct hypotheses."""
    problems: list[str] = []
    if [c.variant_id for c in concepts] != [variant_id(i) for i in range(len(concepts))]:
        problems.append("variant ids must be A, B, C... in order")
    if len({c.hypothesis for c in concepts}) != len(concepts):
        problems.append("every concept needs a distinct hypothesis")
    return problems


def _grounding_problems(concepts: tuple[CreativeConcept, ...], brief: Brief) -> list[str]:
    return [
        f"concept {concept.variant_id} {violation.describe()}"
        for concept in concepts
        for violation in find_violations(concept, brief)
    ]
