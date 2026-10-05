"""``GeminiPlanner``: FR-02's ``plan_variants`` on top of :class:`GeminiClient`."""

import asyncio
from pathlib import Path

from preflight.contracts import Brief, CreativeConcept, PlanNotes
from preflight.errors import PreflightValidationError
from preflight.llm import GeminiClient, MediaPart
from preflight.storage import ProjectStore

from .archetypes import archetypes_for
from .draft import PlanDraft, assemble_concepts, plan_notes
from .prompts import SYSTEM_PROMPT, build_plan_parts
from .screens import ScreenImage, inspect_screen
from .validation import plan_problems


class GeminiPlanner:
    """Implements ``ports.Planner``: distinct, source-backed concepts from a brief."""

    def __init__(self, client: GeminiClient, store: ProjectStore) -> None:
        """Screenshots are read from the brief's project directory in ``store``."""
        self._client = client
        self._store = store
        self.last_notes = PlanNotes()

    async def plan_variants(self, brief: Brief, *, count: int) -> tuple[CreativeConcept, ...]:
        """Return ``count`` concepts with hypotheses assigned in a fixed order.

        Raises:
            PreflightValidationError: ``count`` is unsupported, a screenshot is unreadable, or
                the model's plan is still invalid (schema, screenshot index, or text not found in
                its source field) after one repair.
            ProviderError: Gemini failed.
        """
        archetypes = archetypes_for(count)
        screenshots = await asyncio.gather(
            *(self._load(brief.project_id, name) for name in brief.screenshots)
        )
        draft = await self._client.generate_json(
            PlanDraft,
            SYSTEM_PROMPT,
            build_plan_parts(brief, archetypes, screenshots),
            validate=lambda plan: plan_problems(plan, brief, archetypes),
        )
        screens = await asyncio.to_thread(_inspect, draft, screenshots)
        self.last_notes = plan_notes(draft, brief, screens)
        crops = {index: s.crop for index, s in screens.items() if s.crop is not None}
        return assemble_concepts(draft, brief, archetypes, crops)

    async def _load(self, project_id: str, relative_path: str) -> MediaPart:
        root = self._store.paths(project_id).root.resolve()
        path = (root / relative_path).resolve()
        if not path.is_relative_to(root):
            raise PreflightValidationError(f"screenshot path escapes the project: {relative_path}")
        return await asyncio.to_thread(_read_screenshot, path)


def _inspect(draft: PlanDraft, screenshots: list[MediaPart]) -> dict[int, ScreenImage]:
    """Pixel size of every screenshot and the display to cut out of each mockup."""
    boxes = {note.index: note.device_box for note in draft.screenshots}
    screens: dict[int, ScreenImage] = {}
    for index, part in enumerate(screenshots):
        try:
            screens[index] = inspect_screen(part.data, boxes.get(index))
        except (OSError, ValueError):
            continue
    return screens


def _read_screenshot(path: Path) -> MediaPart:
    try:
        return MediaPart.from_file(path)
    except FileNotFoundError as exc:
        raise PreflightValidationError(f"screenshot not found: {path.name}") from exc
