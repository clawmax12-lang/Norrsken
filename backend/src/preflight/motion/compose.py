"""Build a 60 fps MotionSpec from a concept and accepted extractions. Seconds stay aligned."""

from pydantic import ValidationError

from preflight.contracts import Brief, BriefField, CreativeConcept, Theme
from preflight.contracts._base import VIDEO_DURATION_S
from preflight.generation.end_card import end_card_fields
from preflight.timing import END_CARD_S, MIN_END_CARD_S

from .scene import MOTION_FPS, ExtractedLayers, MotionShot, MotionSpec


def compose_motion(
    concept: CreativeConcept,
    theme: Theme,
    extractions: dict[str, ExtractedLayers],
    brief: Brief | None = None,
) -> MotionSpec | None:
    """Return a tiled MotionSpec, or None when a body scene cannot be reconstructed.

    The last shot is the locked end card: it does not need Vision layers.
    """
    body = concept.scenes[:-1]
    if not body:
        return None
    card = (
        end_card_fields(brief, concept)
        if brief is not None
        else {
            "wordmark": concept.cta,
            "headline": concept.cta,
            "headline_source_field": concept.cta_source_field.value,
            "cta": concept.cta,
            "logo": None,
        }
    )
    card_start = round((VIDEO_DURATION_S - END_CARD_S) * MOTION_FPS)
    total = round(VIDEO_DURATION_S * MOTION_FPS)
    original_body_end = body[-1].t_end
    scale = (VIDEO_DURATION_S - END_CARD_S) / original_body_end if original_body_end else 1.0
    shots: list[MotionShot] = []
    cursor = 0
    for index, scene in enumerate(body):
        extracted = extractions.get(scene.screenshot)
        if extracted is None or extracted.skipped or not extracted.layers:
            return None
        end_frame = min(card_start, max(cursor + 1, round(scene.t_end * scale * MOTION_FPS)))
        hook = index == 0
        shots.append(
            MotionShot(
                screenshot=scene.screenshot,
                start_frame=cursor,
                end_frame=end_frame,
                text=concept.hook if hook else scene.text,
                source_field=concept.hook_source_field if hook else scene.source_field,
                layers=extracted.layers,
                t_start=cursor / MOTION_FPS,
                t_end=end_frame / MOTION_FPS,
            )
        )
        cursor = end_frame
    shots[-1] = shots[-1].model_copy(
        update={"end_frame": card_start, "t_end": card_start / MOTION_FPS}
    )
    cursor = card_start
    if (total - cursor) / MOTION_FPS < MIN_END_CARD_S:
        return None
    last_scene = concept.scenes[-1]
    headline_field = BriefField(str(card["headline_source_field"]))
    shots.append(
        MotionShot(
            screenshot=last_scene.screenshot,
            start_frame=cursor,
            end_frame=total,
            text=str(card["headline"]),
            source_field=headline_field,
            layers=(),
            t_start=cursor / MOTION_FPS,
            t_end=VIDEO_DURATION_S,
        )
    )
    try:
        return MotionSpec(
            variant_id=concept.variant_id,
            theme=theme,
            shots=tuple(shots),
            cta=str(card["cta"]),
            cta_source_field=concept.cta_source_field,
            wordmark=str(card["wordmark"]),
            headline=str(card["headline"]),
            headline_source_field=headline_field,
            logo=card["logo"],
            underlay=False,
        )
    except ValidationError:
        return None
