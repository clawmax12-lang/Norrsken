"""Test-only builders for valid contract objects. Never imported by application code."""

from datetime import UTC, datetime
from typing import Any

from preflight.contracts import (
    Brief,
    BriefField,
    CreativeConcept,
    Goal,
    Scene,
    SimulationResult,
    SimulatorName,
)

SHA = "a" * 64
FIXED_NOW = datetime(2026, 10, 3, 12, 0, tzinfo=UTC)


def make_brief(**overrides: Any) -> Brief:
    """A valid brief for a fictional product used only in tests."""
    data: dict[str, Any] = {
        "project_id": "proj-1",
        "product_name": "Acme Notes",
        "one_liner": "Notes that organise themselves",
        "screenshots": ("uploads/1.png", "uploads/2.png", "uploads/3.png"),
        "goal": Goal.SIGNUPS,
        "audience": "busy startup founders",
    }
    return Brief(**{**data, **overrides})


def make_concept(variant_id: str = "A", **overrides: Any) -> CreativeConcept:
    """A valid 5-scene concept: scenes of 3 seconds each."""
    scenes = tuple(
        Scene(
            t_start=3 * i,
            t_end=3 * (i + 1),
            screenshot=f"uploads/{i % 3 + 1}.png",
            text="Notes that organise themselves",
            source_field=BriefField.ONE_LINER,
        )
        for i in range(5)
    )
    data: dict[str, Any] = {
        "variant_id": variant_id,
        "hypothesis": "outcome first",
        "hook": "Notes that organise themselves",
        "hook_source_field": BriefField.ONE_LINER,
        "scenes": scenes,
        "cta": "Acme Notes",
        "cta_source_field": BriefField.PRODUCT_NAME,
    }
    return CreativeConcept(**{**data, **overrides})


def make_result(
    variant_id: str = "A",
    simulator: SimulatorName = SimulatorName.GEMINI_PANEL,
    values: tuple[float, ...] = (0.5,) * 15,
    **overrides: Any,
) -> SimulationResult:
    """A valid 1 Hz, 15 s simulation result whose primary series is ``values``."""
    data: dict[str, Any] = {
        "variant_id": variant_id,
        "simulator": simulator,
        "version": "test",
        "video_sha256": SHA,
        "duration_s": 15.0,
        "timestamps_s": tuple(float(i) for i in range(len(values))),
        "series": {"signal": values},
        "primary_series": "signal",
    }
    return SimulationResult(**{**data, **overrides})
