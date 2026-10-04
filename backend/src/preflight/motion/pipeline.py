"""Try Mode 2; return None so RenderStage can keep the Showcase MP4."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Protocol

from preflight.contracts import Brief, CompositionSpec, CreativeConcept, RenderMode, RenderResult

from .compose import compose_motion
from .extract import extract_screenshot
from .scene import ExtractedLayers, MotionSpec

if TYPE_CHECKING:
    from pathlib import Path

    from preflight.llm import GeminiClient
    from preflight.storage import ProjectPaths, ProjectStore

_LOG = logging.getLogger(__name__)


class MotionRenderer(Protocol):
    """Isolated 60 fps render entry. Not the Showcase ``Renderer`` port."""

    async def render_motion(self, spec: MotionSpec, output: Path) -> RenderResult:
        """Render ``spec`` to ``output``."""
        ...


class MotionPipeline:
    """Extract + compose + render_motion. Any gap returns None (Showcase fallback)."""

    def __init__(
        self,
        client: GeminiClient | None = None,
        renderer: MotionRenderer | None = None,
        store: ProjectStore | None = None,
    ) -> None:
        """``client``/``renderer``/``store`` are required for Mode 2; without them, skip."""
        self._client = client
        self._renderer = renderer
        self._store = store

    async def ready_for_all(
        self,
        brief: Brief,
        concepts: tuple[CreativeConcept, ...],
        showcase_theme_of: dict[str, CompositionSpec],
        paths: ProjectPaths,
    ) -> bool:
        """True only when every variant can compose a MotionSpec, so the run stays one track."""
        if not concepts:
            return False
        for concept in concepts:
            spec = await self.try_compose(
                brief, concept, showcase_theme_of[concept.variant_id], paths
            )
            if spec is None:
                return False
        return True

    async def try_compose(
        self,
        brief: Brief,
        concept: CreativeConcept,
        showcase: CompositionSpec,
        paths: ProjectPaths,
    ) -> MotionSpec | None:
        """Extract and persist a MotionSpec, or None to keep Showcase."""
        if brief.render_mode is not RenderMode.GENERATIVE_MOTION:
            return None
        if self._client is None or self._store is None:
            _LOG.info("Motion skip %s: extractor unavailable", concept.variant_id)
            return None
        try:
            extractions = await self._extract_all(brief, concept, paths)
            spec_path = paths.motion_spec(concept.variant_id)
            spec_path.unlink(missing_ok=True)
            spec = compose_motion(concept, showcase.theme, extractions, brief)
            if spec is None:
                _LOG.info("Motion skip %s: compose rejected extraction", concept.variant_id)
                return None
            self._store.write(spec_path, spec)
            return spec
        except Exception:
            _LOG.exception("Motion skip %s: unexpected failure; using Showcase", concept.variant_id)
            return None

    async def try_render(
        self,
        brief: Brief,
        concept: CreativeConcept,
        showcase: CompositionSpec,
        paths: ProjectPaths,
        output: Path,
    ) -> RenderResult | None:
        """Render generative motion, or None to keep Showcase bytes."""
        if self._renderer is None:
            _LOG.info("Motion skip %s: renderer unavailable", concept.variant_id)
            return None
        spec_path = paths.motion_spec(concept.variant_id)
        spec = None
        if self._store is not None and spec_path.is_file():
            spec = self._store.read(spec_path, MotionSpec)
        if spec is None:
            spec = await self.try_compose(brief, concept, showcase, paths)
        if spec is None:
            return None
        try:
            return await self._renderer.render_motion(spec, output)
        except Exception:
            _LOG.exception("Motion skip %s: unexpected failure; using Showcase", concept.variant_id)
            return None

    async def _extract_all(
        self, brief: Brief, concept: CreativeConcept, paths: ProjectPaths
    ) -> dict[str, ExtractedLayers]:
        assert self._client is not None and self._store is not None
        found: dict[str, ExtractedLayers] = {}
        for scene in concept.scenes[:-1] or concept.scenes:
            if scene.screenshot in found:
                continue
            image = (paths.root / scene.screenshot).resolve()
            if not image.is_relative_to(paths.root.resolve()):
                found[scene.screenshot] = ExtractedLayers(
                    screenshot=scene.screenshot, layers=(), skipped="path escape"
                )
                continue
            extracted = await extract_screenshot(self._client, brief, image, scene.screenshot)
            self._store.write(paths.extraction(scene.screenshot), extracted)
            found[scene.screenshot] = extracted
        return found
