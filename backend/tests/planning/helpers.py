"""Builders for model answers in planning tests."""

import json
from pathlib import Path

from preflight.contracts import Brief
from preflight.storage import ProjectStore
from tests.factories import make_brief

OUTCOME = {"text": "Notes that organise themselves", "source_field": "one_liner"}
PRODUCT = {"text": "Acme Notes", "source_field": "product_name"}


def scene(index: int, seconds: int, text: dict[str, str] = OUTCOME) -> dict[str, object]:
    return {"screenshot_index": index, "duration_s": seconds, **text}


def concept_json(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "hook": "Notes that organise themselves",
        "hook_source_field": "one_liner",
        "scenes": [
            scene(0, 3),
            scene(1, 3, PRODUCT),
            scene(2, 3),
            scene(0, 3, PRODUCT),
            scene(1, 3),
        ],
        "cta": "Acme Notes",
        "cta_source_field": "product_name",
    }
    return {**data, **overrides}


def plan_json(*concepts: dict[str, object]) -> str:
    """Three concepts with different screenshot orders, unless the caller passes its own."""
    if concepts:
        return json.dumps({"concepts": list(concepts)})
    base = concept_json()
    return json.dumps({"concepts": [_shift_screenshots(base, shift) for shift in range(3)]})


def _shift_screenshots(concept: dict[str, object], shift: int, count: int = 3) -> dict[str, object]:
    scenes = concept["scenes"]
    if not isinstance(scenes, list):
        raise TypeError("concept scenes must be a list")
    shifted: list[dict[str, object]] = []
    for scene in scenes:
        if not isinstance(scene, dict):
            raise TypeError("scene must be an object")
        index = scene["screenshot_index"]
        shifted.append({**scene, "screenshot_index": (int(str(index)) + shift) % count})
    return {**concept, "scenes": shifted}


def project_with_screenshots(tmp_path: Path) -> tuple[Brief, ProjectStore]:
    """A project whose three screenshots exist on disk (distinct bytes per file)."""
    store = ProjectStore(tmp_path)
    paths = store.create("proj-1")
    brief = make_brief()
    for index, name in enumerate(brief.screenshots, start=1):
        target = paths.root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(f"png-{index}".encode())
    return brief, store
