"""RENDERED: generate backdrops, compose, render each variant to MP4 (FR-03, PRD §9.2)."""

from functools import partial

from preflight.contracts import (
    CompositionSpec,
    CreativeConcept,
    GeneratedAsset,
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
    ) -> None:
        """Wire the generation layer; every external call runs under ``policy``."""
        self._generator = generator
        self._composer = composer
        self._renderer = renderer
        self._policy = policy

    async def run(self, ctx: RunContext) -> str:
        """Render pending or previously failed variants; fail only when none survives."""
        pending = [v.variant_id for v in ctx.tracker.record.variants if not _is_rendered(ctx, v)]
        await gather_bounded(
            RENDER_CONCURRENCY, [partial(self._render_one, ctx, i) for i in pending]
        )
        rendered = ctx.rendered_variants()
        if not rendered:
            raise RenderError("no variant rendered successfully")
        return f"Rendered {len(rendered)} of {len(ctx.tracker.record.variants)} variants"

    async def _render_one(self, ctx: RunContext, variant_id: str) -> None:
        concept = ctx.read_concept(variant_id)
        try:
            record = await self._produce(ctx, concept)
        except PreflightError as exc:
            record = VariantRecord(
                variant_id=variant_id, render_status=RenderStatus.FAILED, error=str(exc)
            )
        ctx.tracker.update_variant(record)

    async def _produce(self, ctx: RunContext, concept: CreativeConcept) -> VariantRecord:
        assets = await self._generate_assets(ctx, concept)
        spec = self._composer.compose(ctx.brief, concept, assets)
        ctx.store.write(ctx.paths.spec(concept.variant_id), spec)
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
