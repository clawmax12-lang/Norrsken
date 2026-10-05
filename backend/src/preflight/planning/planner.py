"""``GeminiPlanner``: FR-02's ``plan_variants`` on top of :class:`GeminiClient`."""

import asyncio
import logging
from collections.abc import Sequence
from pathlib import Path

from preflight.contracts import Brief, CreativeConcept, PlanNotes, Reason
from preflight.errors import PreflightValidationError
from preflight.llm import CallUsage, GeminiClient, MediaPart
from preflight.llm.parts import Part, TextPart
from preflight.storage import ProjectStore

from .archetypes import ARCHETYPES, Archetype, archetypes_for
from .draft import PlanDraft, assemble_concepts, plan_notes
from .prompts import SYSTEM_PROMPT, build_plan_parts, rewrite_block
from .screens import ScreenImage, inspect_screen
from .validation import craft_problems, plan_problems, without_unsourced_extras

logger = logging.getLogger(__name__)

PLAN_ATTEMPTS = 2


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
                its source field) after one repair, ``PLAN_ATTEMPTS`` times.
            ProviderError: Gemini failed.
        """
        archetypes = archetypes_for(count)
        screenshots = await self._screenshots(brief)
        draft, _ = await self._draft(
            brief, archetypes, build_plan_parts(brief, archetypes, screenshots)
        )
        screens = await asyncio.to_thread(_inspect, draft, screenshots)
        self.last_notes = plan_notes(draft, brief, screens)
        return assemble_concepts(draft, brief, archetypes, screens)

    async def rewrite(
        self, brief: Brief, winner: CreativeConcept, reasons: Sequence[Reason]
    ) -> tuple[CreativeConcept, CallUsage]:
        """The pretest's winner rewritten as the final ad, held to every plan rule.

        Same angle and variant id; the model may reorder scenes, pick other screens and
        rewrite the hook, voice and end card. Claims are checked against the brief as in a run.

        Raises:
            PreflightValidationError: the rewrite is still invalid after its repairs.
            ProviderError: Gemini failed.
        """
        archetype = next(
            (a for a in ARCHETYPES if a.name == winner.hypothesis),
            Archetype(winner.hypothesis, winner.angle or "Keep the winner's angle."),
        )
        screenshots = await self._screenshots(brief)
        parts = build_plan_parts(brief, (archetype,), screenshots)
        parts.insert(1, TextPart(rewrite_block(winner, reasons)))
        draft, usage = await self._draft(brief, (archetype,), parts, attempts=1)
        screens = await asyncio.to_thread(_inspect, draft, screenshots)
        (concept,) = assemble_concepts(draft, brief, (archetype,), screens)
        return concept.model_copy(update={"variant_id": winner.variant_id}), usage

    async def _draft(
        self,
        brief: Brief,
        archetypes: tuple[Archetype, ...],
        parts: list[Part],
        attempts: int = PLAN_ATTEMPTS,
    ) -> tuple[PlanDraft, CallUsage]:
        for attempt in range(1, attempts + 1):
            checks = 0

            def validate(plan: PlanDraft) -> list[str]:
                # The first answer hears every rule; the repair is held only to the ones that
                # keep the film truthful and timed, so a missed craft rule does not end the run.
                nonlocal checks
                checks += 1
                return plan_problems(plan, brief, archetypes, craft=checks == 1)

            try:
                answer = await self._client.generate_json_measured(
                    PlanDraft, SYSTEM_PROMPT, parts, validate=validate
                )
                break
            except PreflightValidationError:
                if attempt == attempts:
                    raise
                logger.warning("Plan still invalid after its repair, planning afresh")
        draft = without_unsourced_extras(answer.value, brief)
        missed = craft_problems(draft, brief)
        if missed:
            logger.warning("Plan accepted with craft rules missed: %s", "; ".join(missed))
        return draft, answer.usage

    async def _screenshots(self, brief: Brief) -> list[MediaPart]:
        return list(
            await asyncio.gather(
                *(self._load(brief.project_id, name) for name in brief.screenshots)
            )
        )

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
