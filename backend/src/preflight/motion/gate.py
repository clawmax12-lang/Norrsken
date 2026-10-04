"""Fail-closed filters: drop unsure layers; reject a scene that cannot be reconstructed."""

from preflight.contracts import Brief, BriefField
from preflight.planning.grounding import ungrounded_words

from .scene import CONFIDENCE_MIN, MIN_LAYERS, ExtractedLayers, LayerKind, MotionLayer


def allowed_label_source(brief: Brief) -> str:
    """Labels may only reuse product name, one-liner and optional CTA words."""
    return " ".join(
        part
        for part in (
            brief.field_text(BriefField.PRODUCT_NAME),
            brief.field_text(BriefField.ONE_LINER),
            brief.field_text(BriefField.GOAL_NOTE),
        )
        if part
    )


def ground_layer(layer: MotionLayer, brief: Brief) -> MotionLayer:
    """Keep geometry; strip a label that is not source-backed."""
    if not layer.label:
        return layer
    extra = ungrounded_words(layer.label, allowed_label_source(brief))
    if extra:
        return layer.model_copy(update={"label": None})
    return layer


def keep_layers(
    layers: tuple[MotionLayer, ...], brief: Brief, *, require_chart: bool = False
) -> tuple[MotionLayer, ...]:
    """Drop low-confidence layers, then ground remaining labels."""
    kept = tuple(
        ground_layer(layer, brief) for layer in layers if layer.confidence >= CONFIDENCE_MIN
    )
    if require_chart and not any(layer.kind is LayerKind.CHART for layer in kept):
        return ()
    if len(kept) < MIN_LAYERS:
        return ()
    if not _readable_product_ui(kept):
        return ()
    return kept


def _readable_product_ui(layers: tuple[MotionLayer, ...]) -> bool:
    """Reject fragment clouds from lifestyle 3D heroes that look like debug boxes."""
    areas = [layer.bbox_norm[2] * layer.bbox_norm[3] for layer in layers]
    if not areas:
        return False
    largest = max(areas)
    if largest < 0.12:
        return False
    tiny = sum(1 for area in areas if area < 0.05)
    return not (tiny >= 6 and largest < 0.22)


def accept_extraction(
    extracted: ExtractedLayers, brief: Brief, *, require_chart: bool = False
) -> bool:
    """True when the screenshot yielded enough grounded geometry to animate."""
    if extracted.skipped:
        return False
    return bool(keep_layers(extracted.layers, brief, require_chart=require_chart))
