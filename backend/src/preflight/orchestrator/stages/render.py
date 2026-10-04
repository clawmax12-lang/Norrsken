"""RENDERED: generate backdrops, compose, render each variant to MP4 (FR-03, PRD §9.2)."""

from functools import partial
from typing import TYPE_CHECKING

from preflight.contracts import (
    CompositionSpec,
    CreativeConcept,
    GeneratedAsset,
    RenderMode,
    RenderStatus,
    RunState,
    Step,
    VariantRecord,
)
from preflight.errors import PreflightError, RenderError, TransientProviderError
from preflight.orchestrator.concurrency import gather_bounded
from preflight.orchestrator.context import RunContext
from preflight.orchestrator.retry import StepPolicy
from preflight.ports import AssetGenerator, Composer, Renderer

if TYPE_CHECKING:
    from preflight.motion import MotionPipeline

RENDER_CONCURRENCY = 2
_RETRYABLE = (TransientProviderError, RenderError)


class RenderStage:
    """Renders every variant that is not rendered yet; one failed render never stops the run."""

    step = Step.RENDER
    completes = RunState.RENDERED
    title = "Rendering videos"

    def __init__(
        self,
        generator: AssetGenerator,
        composer: Composer,
        renderer: Renderer,
        policy: StepPolicy,
        motion: "MotionPipeline | None" = None,
    ) -> None:
        """Wire the generation layer; every external call runs under ``policy``."""
        self._generator = generator
        self._composer = composer
        self._renderer = renderer
        self._policy = policy
        self._motion = motion

    async def run(self, ctx: RunContext) -> str:
        """Render pending or previously failed variants; fail only when none survives."""
        pending = [v.variant_id for v in ctx.tracker.record.variants if not _is_rendered(ctx, v)]
        allow_motion = await self._lock_track(ctx, pending)
        await gather_bounded(
            RENDER_CONCURRENCY,
            [partial(self._render_one, ctx, i, allow_motion) for i in pending],
        )
        rendered = ctx.rendered_variants()
        if not rendered:
            raise RenderError("no variant rendered successfully")
        return f"Rendered {len(rendered)} of {len(ctx.tracker.record.variants)} variants"

    async def _lock_track(self, ctx: RunContext, pending: list[str]) -> bool:
        """Use Mode 2 only when every pending variant can compose; otherwise all Showcase."""
        if (
            ctx.brief.render_mode is not RenderMode.GENERATIVE_MOTION
            or self._motion is None
            or not pending
        ):
            return False
        showcases: dict[str, CompositionSpec] = {}
        concepts: list[CreativeConcept] = []
        for variant_id in pending:
            concept = ctx.read_concept(variant_id)
            concepts.append(concept)
            spec = await self._ensure_spec(ctx, concept)
            showcases[variant_id] = spec
        ready = await self._motion.ready_for_all(
            ctx.brief, tuple(concepts), showcases, ctx.paths
        )
        if not ready:
            ctx.log.skipped(
                Step.RENDER,
                "Motion not ready for every variant; using Showcase for all",
            )
            for variant_id in pending:
                ctx.paths.motion_spec(variant_id).unlink(missing_ok=True)
        return ready

    async def _render_one(self, ctx: RunContext, variant_id: str, allow_motion: bool) -> None:
        concept = ctx.read_concept(variant_id)
        try:
            record = await self._produce(ctx, concept, allow_motion)
        except PreflightError as exc:
            record = VariantRecord(
                variant_id=variant_id, render_status=RenderStatus.FAILED, error=str(exc)
            )
        ctx.tracker.update_variant(record)

    async def _ensure_spec(self, ctx: RunContext, concept: CreativeConcept) -> CompositionSpec:
        path = ctx.paths.spec(concept.variant_id)
        if path.is_file():
            return ctx.store.read(path, CompositionSpec)
        assets = await self._generate_assets(ctx, concept)
        spec = self._composer.compose(ctx.brief, concept, assets)
        ctx.store.write(path, spec)
        return spec

    async def _produce(
        self, ctx: RunContext, concept: CreativeConcept, allow_motion: bool
    ) -> VariantRecord:
        spec = await self._ensure_spec(ctx, concept)
        if allow_motion and self._motion is not None:
            output = ctx.paths.video(concept.variant_id)
            output.parent.mkdir(parents=True, exist_ok=True)
            motion = await self._motion.try_render(ctx.brief, concept, spec, ctx.paths, output)
            if motion is not None:
                ctx.log.skipped(
                    Step.RENDER,
                    f"Motion rendered variant {concept.variant_id}; Showcase spec kept",
                    variant_id=concept.variant_id,
                )
                return VariantRecord(
                    variant_id=concept.variant_id,
                    render_status=RenderStatus.RENDERED,
                    video_path=str(output.relative_to(ctx.paths.root)),
                    video_sha256=motion.video_sha256,
                    render_seconds=motion.render_seconds,
                )
            ctx.log.skipped(
                Step.RENDER,
                f"Motion skipped for variant {concept.variant_id}; using Showcase",
                variant_id=concept.variant_id,
            )
        return await self._render(ctx, spec)

    async def _generate_assets(
        self, ctx: RunContext, concept: CreativeConcept
    ) -> tuple[GeneratedAsset, ...]:
        """Generate backdrops; on any failure fall back to template-only backgrounds."""
        variant_id = concept.variant_id
        title = f"Generating backgrounds for variant {variant_id}"
        with ctx.log.step(Step.GENERATE, title, variant_id=variant_id) as handle:
            generate = partial(
                self._generator.generate, ctx.brief, concept, ctx.paths.assets / variant_id
            )
            try:
                assets = await self._policy.run(generate)
            except PreflightError as exc:
                handle.skip(f"Backgrounds unavailable ({exc}); using template-only backgrounds")
                return ()
            handle.report(f"Generated {len(assets)} backgrounds for variant {variant_id}")
            return assets

    async def _render(self, ctx: RunContext, spec: CompositionSpec) -> VariantRecord:
        variant_id = spec.variant_id
        output = ctx.paths.video(variant_id)
        output.parent.mkdir(parents=True, exist_ok=True)
        with ctx.log.step(
            Step.RENDER, f"Rendering variant {variant_id}", variant_id=variant_id
        ) as handle:
            render = partial(self._renderer.render, spec, output)
            result = await self._policy.run(render, retry_on=_RETRYABLE)
            if not output.is_file():
                raise RenderError(f"renderer reported success but wrote no file: {output}")
            handle.report(f"Rendered variant {variant_id} in {result.render_seconds:.1f}s")
        return VariantRecord(
            variant_id=variant_id,
            render_status=RenderStatus.RENDERED,
            video_path=str(output.relative_to(ctx.paths.root)),
            video_sha256=result.video_sha256,
            render_seconds=result.render_seconds,
        )


def _is_rendered(ctx: RunContext, variant: VariantRecord) -> bool:
    done = variant.render_status is RenderStatus.RENDERED
    return done and ctx.paths.video(variant.variant_id).is_file()
