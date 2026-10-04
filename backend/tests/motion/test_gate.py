from tests.factories import make_brief

from preflight.contracts import BriefField
from preflight.motion.gate import ground_layer, keep_layers
from preflight.motion.scene import LayerKind, MotionLayer


def _layer(**overrides) -> MotionLayer:
    payload = {
        "id": "panel",
        "kind": LayerKind.PANEL,
        "bbox_norm": (0.1, 0.2, 0.4, 0.3),
        "confidence": 0.9,
        "label": None,
        **overrides,
    }
    return MotionLayer(**payload)


def test_low_confidence_layers_are_dropped() -> None:
    brief = make_brief()
    kept = keep_layers(
        (
            _layer(id="ok", confidence=0.9),
            _layer(id="weak", confidence=0.2),
            _layer(id="chart", kind=LayerKind.CHART, confidence=0.8),
        ),
        brief,
    )
    assert tuple(layer.id for layer in kept) == ("ok", "chart")


def test_ocr_number_without_brief_source_is_stripped() -> None:
    brief = make_brief(one_liner="Notes that organise themselves")
    layer = ground_layer(_layer(kind=LayerKind.TEXT, label="47% more sales"), brief)
    assert layer.label is None


def test_product_name_label_is_kept() -> None:
    brief = make_brief(product_name="Acme Notes")
    layer = ground_layer(_layer(kind=LayerKind.BUTTON, label="Acme Notes"), brief)
    assert layer.label == "Acme Notes"


def test_missing_chart_when_required_rejects_the_scene() -> None:
    brief = make_brief()
    kept = keep_layers(
        (_layer(id="a", confidence=0.9), _layer(id="b", confidence=0.9)),
        brief,
        require_chart=True,
    )
    assert kept == ()


def test_tiny_lifestyle_fragments_are_rejected() -> None:
    brief = make_brief()
    fragments = tuple(
        _layer(id=f"bit-{i}", bbox_norm=(0.05 * i, 0.08 * i, 0.04, 0.04), confidence=0.9)
        for i in range(8)
    )
    assert keep_layers(fragments, brief) == ()


def test_ungrounded_words_do_not_use_audience_as_a_label_source() -> None:
    brief = make_brief(audience="busy startup founders")
    layer = ground_layer(_layer(label="busy startup founders"), brief)
    assert layer.label is None
    assert BriefField.AUDIENCE.value == "audience"
