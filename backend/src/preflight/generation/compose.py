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
    CompositionSpec,
    CreativeConcept,
    GeneratedAsset,
    Layout,
    Scene,
    SceneSpec,
    Transition,
)
from preflight.contracts._base import VIDEO_FPS
from preflight.errors import PreflightValidationError

from .theme import theme_for

# After the hook, scenes alternate a centred device with a floating one.
_DEVICE_LAYOUTS = (Layout.DEVICE_CENTER, Layout.DEVICE_FLOAT)
_TRANSITIONS = (Transition.SCALE, Transition.PUSH, Transition.FADE)
# A scene fades into the next over this many frames (kept equal to the renderer's overlap).
_TRANSITION_FRAMES = 14


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
    boundaries = _frame_boundaries(concept)
    scenes = tuple(
        _scene_spec(concept, scene, index, (boundaries[index], boundaries[index + 1]), assets)
        for index, scene in enumerate(concept.scenes)
    )
    return CompositionSpec(
        variant_id=concept.variant_id,
        duration_frames=boundaries[-1],
        theme=theme_for(brief.brand_color),
        scenes=scenes,
        cta=concept.cta,
        cta_source_field=concept.cta_source_field,
    )


class TemplateComposer:
    """:class:`preflight.ports.Composer` backed by :func:`compose` (the single template)."""

    def compose(
        self, brief: Brief, concept: CreativeConcept, assets: Sequence[GeneratedAsset]
    ) -> CompositionSpec:
        """Delegate to the pure function so it can be wired through the port."""
        return compose(brief, concept, assets)


def _frame_boundaries(concept: CreativeConcept) -> tuple[int, ...]:
    """Scene edges in frames; scene ``i`` spans ``[edges[i], edges[i + 1])``."""
    edges = [round(scene.t_start * VIDEO_FPS) for scene in concept.scenes]
    edges.append(concept.duration_s * VIDEO_FPS)
    if any(later <= earlier for earlier, later in itertools.pairwise(edges)):
        raise PreflightValidationError(
            f"scenes of variant {concept.variant_id} are shorter than one frame at {VIDEO_FPS} fps"
        )
    return tuple(edges)


def _scene_spec(
    concept: CreativeConcept,
    scene: Scene,
    index: int,
    frames: tuple[int, int],
    assets: Sequence[GeneratedAsset],
) -> SceneSpec:
    start, end = frames
    is_hook = index == 0
    return SceneSpec(
        start_frame=start,
        end_frame=end,
        text=concept.hook if is_hook else scene.text,
        source_field=concept.hook_source_field if is_hook else scene.source_field,
        screenshot=scene.screenshot,
        layout=Layout.TEXT_ONLY if is_hook else _DEVICE_LAYOUTS[(index - 1) % len(_DEVICE_LAYOUTS)],
        transition_in=Transition.CUT if is_hook else _TRANSITIONS[(index - 1) % len(_TRANSITIONS)],
        backdrop=_backdrop_for(assets, index, end - start + _TRANSITION_FRAMES),
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
