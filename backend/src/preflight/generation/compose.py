"""FR-03 composition: map a concept onto the one template as a validated ``CompositionSpec``.

Pure and deterministic: the same brief, concept and assets always give the same spec. Every
string on screen is copied from the concept (whose copy is already source-grounded), so the
composer cannot introduce a claim. The first scene is the hook; later scenes alternate
layouts and transitions so a 15 s video has rhythm without any randomness.
"""

import itertools
from collections.abc import Sequence

from preflight.contracts import (
    AssetKind,
    Brief,
    BriefField,
    CompositionSpec,
    CreativeConcept,
    GeneratedAsset,
    Layout,
    Scene,
    SceneSpec,
    Transition,
)
from preflight.contracts._base import VIDEO_DURATION_S, VIDEO_FPS
from preflight.errors import PreflightValidationError
from preflight.timing import END_CARD_S, MIN_END_CARD_S

from .end_card import end_card_fields
from .theme import theme_for

# After the hook, scenes alternate a centred device with a floating one.
_DEVICE_LAYOUTS = (Layout.DEVICE_CENTER, Layout.DEVICE_FLOAT)
_TRANSITIONS = (Transition.SCALE, Transition.PUSH, Transition.FADE)
# A scene fades into the next over this many frames (must equal renderer TRANSITION_FRAMES).
TRANSITION_FRAMES = 20


def compose(
    brief: Brief, concept: CreativeConcept, assets: Sequence[GeneratedAsset]
) -> CompositionSpec:
    """Build the spec Remotion renders for ``concept``.

    Args:
        brief: Supplies the optional brand colour for the theme.
        concept: Scenes, hook and CTA; all on-screen text comes from here.
        assets: Generated backdrops (possibly none: the template then draws its own).

    Raises:
        PreflightValidationError: Two scene boundaries fall on the same frame at 30 fps.
    """
    card = end_card_fields(brief, concept)
    boundaries = _frame_boundaries(concept)
    last_index = len(concept.scenes) - 1
    scenes = tuple(
        _scene_spec(
            concept,
            scene,
            index,
            last_index,
            (boundaries[index], boundaries[index + 1]),
            assets,
        )
        for index, scene in enumerate(concept.scenes)
    )
    return CompositionSpec(
        variant_id=concept.variant_id,
        duration_frames=boundaries[-1],
        theme=theme_for(brief.brand_color),
        scenes=scenes,
        cta=str(card["cta"]),
        cta_source_field=concept.cta_source_field,
        wordmark=str(card["wordmark"]),
        headline=str(card["headline"]),
        headline_source_field=BriefField(str(card["headline_source_field"])),
        logo=card["logo"],
    )


class TemplateComposer:
    """:class:`preflight.ports.Composer` backed by :func:`compose` (the single template)."""

    def compose(
        self, brief: Brief, concept: CreativeConcept, assets: Sequence[GeneratedAsset]
    ) -> CompositionSpec:
        """Delegate to the pure function so it can be wired through the port."""
        return compose(brief, concept, assets)


def _frame_boundaries(concept: CreativeConcept) -> tuple[int, ...]:
    """Scene edges in frames; the last scene is the locked end-card window."""
    ends = [round(scene.t_end * VIDEO_FPS) for scene in concept.scenes]
    total = concept.duration_s * VIDEO_FPS
    if len(concept.scenes) == 1:
        edges = [0, total]
    else:
        body_end = round((VIDEO_DURATION_S - END_CARD_S) * VIDEO_FPS)
        original = ends[-2] if ends[-2] > 0 else body_end
        scale = body_end / original
        edges = [0]
        for end in ends[:-1]:
            edges.append(max(edges[-1] + 1, round(end * scale)))
        edges[-1] = body_end
        edges.append(total)
        last_len = (edges[-1] - edges[-2]) / VIDEO_FPS
        if last_len < MIN_END_CARD_S:
            raise PreflightValidationError(
                f"end card of variant {concept.variant_id} is {last_len:.2f}s; "
                f"need {MIN_END_CARD_S}s"
            )
    if any(later <= earlier for earlier, later in itertools.pairwise(edges)):
        raise PreflightValidationError(
            f"scenes of variant {concept.variant_id} are shorter than one frame at {VIDEO_FPS} fps"
        )
    return tuple(edges)


def _scene_spec(
    concept: CreativeConcept,
    scene: Scene,
    index: int,
    last_index: int,
    frames: tuple[int, int],
    assets: Sequence[GeneratedAsset],
) -> SceneSpec:
    start, end = frames
    is_hook = index == 0
    is_end = index == last_index
    if is_hook:
        layout = Layout.TEXT_ONLY
        transition = Transition.FADE
    elif is_end:
        layout = Layout.DEVICE_CENTER
        transition = Transition.FADE
    else:
        layout = _DEVICE_LAYOUTS[(index - 1) % len(_DEVICE_LAYOUTS)]
        transition = _TRANSITIONS[(index - 1) % len(_TRANSITIONS)]
    return SceneSpec(
        start_frame=start,
        end_frame=end,
        text=concept.hook if is_hook else scene.text,
        source_field=concept.hook_source_field if is_hook else scene.source_field,
        screenshot=scene.screenshot,
        layout=layout,
        transition_in=transition,
        backdrop=_backdrop_for(assets, index, end - start + TRANSITION_FRAMES),
    )


def _backdrop_for(
    assets: Sequence[GeneratedAsset], index: int, scene_frames: int
) -> GeneratedAsset | None:
    """Round-robin over assets; a clip is used only if it lasts the whole scene."""
    if not assets:
        return None
    candidate = assets[index % len(assets)]
    if candidate.kind is AssetKind.VIDEO and (candidate.duration_s or 0) * VIDEO_FPS < scene_frames:
        return None
    return candidate
